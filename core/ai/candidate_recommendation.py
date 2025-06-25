# AI logic for candidate recommendations for recruiters
# Placeholder for actual ML model integration

import numpy as np
import os
from catboost import CatBoostClassifier
from typing import List, Dict, Any, Tuple
from django.conf import settings
from ml_training.feature_extraction import (
    jaccard_similarity, 
    skills_overlap,
    education_match,
    location_match,
    preferred_job_type_match
)
from ml_training.enhanced_matching import (
    normalize_skills,
    extract_experience_years,
    education_level_score,
    job_type_match,
    enhanced_location_match,
    get_matching_skills
)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/candidate_recommendation_model.cbm')
candidate_catboost_model = CatBoostClassifier()
candidate_catboost_model.load_model(MODEL_PATH)

FEATURE_ORDER = [
    "skills_jaccard",
    "skills_overlap",
    "education_match",
    "experience_years",
    "job_experience_required",
    "experience_gap",
    "preferred_job_type_match",
    "location_match",
    "salary_within_range",
    "seeker_rating",
    "is_available",
]

from core.ai.feature_extraction import as_dict_job_seeker, as_dict_job

def extract_candidate_features(seeker, job):
    """Extract features for candidate recommendation model"""
    seeker_dict = as_dict_job_seeker(seeker)
    job_dict = as_dict_job(job)
    
    # Extract features manually
    features = {}
    
    # Skills features
    seeker_skills = normalize_skills(seeker_dict.get("skills", []))
    job_skills = normalize_skills(job_dict.get("skills", []))
    
    if seeker_skills and job_skills:
        features["skills_jaccard"] = jaccard_similarity(seeker_skills, job_skills)
        features["skills_overlap"] = skills_overlap(seeker_skills, job_skills)
    else:
        features["skills_jaccard"] = 0.0
        features["skills_overlap"] = 0.0
    
    # Education match
    features["education_match"] = education_level_score(
        seeker_dict.get("education", {}),
        job_dict.get("requirements", [])
    ) if seeker_dict.get("education") and job_dict.get("requirements") else 0.0
    
    # Experience features
    seeker_exp_years = extract_experience_years(seeker_dict.get("experience", []))
    job_min_exp = job_dict.get("min_experience", 0)
    
    features["experience_years"] = seeker_exp_years
    features["job_experience_required"] = job_min_exp
    features["experience_gap"] = max(0, job_min_exp - seeker_exp_years) if job_min_exp > 0 else 0
    
    # Job type match
    features["preferred_job_type_match"] = job_type_match(
        seeker_dict.get("preferred_job_types", []),
        job_dict.get("job_type", "")
    )
    
    # Location match
    features["location_match"] = enhanced_location_match(
        seeker_dict.get("location", ""),
        job_dict.get("location", ""),
        seeker_dict.get("willing_to_relocate", False)
    )
    
    # Salary match
    seeker_min_salary = seeker_dict.get("min_salary", 0)
    job_min_salary = job_dict.get("min_salary", 0)
    job_max_salary = job_dict.get("max_salary", 0)
    
    if seeker_min_salary > 0 and job_max_salary > 0:
        features["salary_within_range"] = 1.0 if seeker_min_salary <= job_max_salary else 0.0
    elif seeker_min_salary > 0 and job_min_salary > 0:
        features["salary_within_range"] = 1.0 if seeker_min_salary <= job_min_salary * 1.2 else 0.0
    else:
        features["salary_within_range"] = 0.5  # Neutral when salary info is missing
    
    # Other features
    features["seeker_rating"] = seeker_dict.get("average_rating", 0) / 5.0 if seeker_dict.get("average_rating") else 0.0
    features["is_available"] = 1.0 if seeker_dict.get("is_available", True) else 0.0
    
    # Return features in the expected order
    return [features.get(f, 0) for f in FEATURE_ORDER]


def rule_based_candidate_recommendation(job, seekers, top_n=10):
    """
    Enhanced rule-based candidate recommendation that doesn't rely on ML models.
    Uses direct matching on skills, education, and location with weighted scoring.
    Enforces strict matching criteria - will return empty list if no good matches.
    
    Args:
        job: The job to find candidates for
        seekers: List of job seekers to consider
        top_n: Number of candidates to return
        
    Returns:
        List of recommended candidates
    """
    # Only consider available seekers
    available_seekers = [s for s in seekers if getattr(s, 'is_available', True)]
    print(f"[DEBUG] Rule-based: {len(available_seekers)} available seekers")
    
    if not available_seekers:
        print("[DEBUG] No available seekers found")
        return []
    
    # Convert job to dict for feature extraction
    job_dict = as_dict_job(job)
    job_skills = job_dict.get("skills", [])
    job_requirements = job_dict.get("requirements", [])  # Get education requirements separately
    job_location = job_dict.get("location", "")
    job_type = job_dict.get("job_type", "")
    job_min_exp = job_dict.get("min_experience", 0)
    
    # Print detailed job info for debugging
    print(f"[DEBUG] Rule-based recommendation for Job ID: {getattr(job, 'id', 'unknown')}, Title: {getattr(job, 'title', 'unknown')}")
    print(f"[DEBUG] Job Skills: {job_skills}")
    print(f"[DEBUG] Job Requirements: {job_requirements}")
    print(f"[DEBUG] Job Experience Level: {job_dict.get('experience_level', 'None')}")
    print(f"[DEBUG] Job Min Experience: {job_min_exp}")
    
    if not job_skills:
        print("[DEBUG] Job has no skills listed, cannot match candidates")
        return []
    
    # Normalize job skills
    normalized_job_skills = normalize_skills(job_skills)
    print(f"[DEBUG] Job skills (normalized): {normalized_job_skills}")
    
    # Score each seeker
    scored_seekers = []
    for seeker in available_seekers:
        seeker_dict = as_dict_job_seeker(seeker)
        seeker_skills = seeker_dict.get("skills", [])
        
        # Skip if seeker has no skills
        if not seeker_skills:
            print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has no skills listed, skipping")
            continue
        
        # Normalize seeker skills
        normalized_seeker_skills = normalize_skills(seeker_skills)
        print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} normalized skills: {normalized_seeker_skills}")
        
        # Get matching skills using enhanced matching with normalized skills
        matching_skills, skills_score = get_matching_skills(normalized_seeker_skills, normalized_job_skills)
        
        # STRICT REQUIREMENT: Must have at least one matching skill
        if not matching_skills:
            print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has no matching skills, skipping")
            continue
            
        print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has matching skills: {matching_skills}, score: {skills_score:.2f}")
        
        # Adjust skills score weight (60% weight) - most important
        skills_score = skills_score * 0.6
        
        # Education match (20% weight) using enhanced education matching
        education_score = education_level_score(seeker_dict.get("education", {}), job_dict.get("requirements", []))
        print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} education score: {education_score:.2f}")
        education_score = education_score * 0.2
        
        # Location match (10% weight) using enhanced location matching
        location_score = 0.0
        if job_location and seeker_dict.get("location"):
            location_score = enhanced_location_match(
                seeker_dict["location"], 
                job_location,
                seeker_dict.get("willing_to_relocate", False)
            ) * 0.1
        
        # Experience match (10% weight) using enhanced experience extraction
        experience_score = 0.0
        seeker_exp_years = extract_experience_years(seeker_dict.get("experience", []))
        
        # STRICT REQUIREMENT: Must meet minimum experience if specified
        # Allow 60% of required experience (reduced from 70% to account for data quality issues)
        if job_min_exp > 0 and seeker_exp_years < job_min_exp * 0.6:
            print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has insufficient experience: {seeker_exp_years} vs required {job_min_exp}")
            continue
            
        if seeker_exp_years >= job_min_exp:
            experience_score = 0.1  # Full score if they meet minimum requirements
        elif job_min_exp > 0 and seeker_exp_years > 0:
            # Partial score if they have some experience but not enough
            experience_score = (seeker_exp_years / job_min_exp) * 0.05  # Half weight for partial match
        
        # Job type match using enhanced job type matching
        job_type_score = 0.0
        if job_type and seeker_dict.get("preferred_job_types"):
            job_type_score = job_type_match(seeker_dict["preferred_job_types"], job_type) * 0.05
        
        # Calculate final score
        score = skills_score + education_score + location_score + experience_score + job_type_score
        
        # Add debug info
        print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} scores: skills={skills_score:.2f}, edu={education_score:.2f}, loc={location_score:.2f}, exp={experience_score:.2f}, type={job_type_score:.2f}")
        
        # STRICT REQUIREMENT: Must have a minimum total score
        if score < 0.3:  # Minimum 30% match required
            print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has insufficient total score: {score:.2f}")
            continue
            
        # Add rating bonus (up to 5% extra)
        rating = getattr(seeker, 'average_rating', 0) or 0
        if rating > 0:
            score += (rating / 5.0) * 0.05
        
        scored_seekers.append((score, seeker))
    
    # Sort by score (highest first)
    scored_seekers.sort(reverse=True, key=lambda x: x[0])
    
    # Print top scores for debugging
    if scored_seekers:
        print(f"[DEBUG] Rule-based top scores: {[round(score, 2) for score, _ in scored_seekers[:5]]}")
    else:
        print("[DEBUG] No candidates met the strict matching criteria")
    
    # Return candidates with good scores, up to top_n
    return [seeker for score, seeker in scored_seekers[:top_n]]


def get_candidate_recommendations_for_job(job, seekers, top_n=10, score_threshold=0.15, explain=False):
    """
    Get candidate recommendations for a job using a hybrid approach:
    1. ML model-based scoring (primary approach)
    2. Rule-based fallback if ML model fails or returns no results
    3. Cold start handling for jobs with minimal data
    
    Args:
        job: The job to find candidates for
        seekers: List of job seekers to consider
        top_n: Maximum number of recommendations to return
        score_threshold: Minimum score threshold for ML recommendations
        explain: Whether to include explanation of scores
        
    Returns:
        List of recommended candidates
    """
    print(f"[DEBUG] Finding candidates for job ID: {job.id}, title: {job.title}")
    print(f"[DEBUG] Total seekers to evaluate: {len(seekers)}")
    
    # Filter to only available seekers first
    available_seekers = [s for s in seekers if getattr(s, 'is_available', True)]
    print(f"[DEBUG] Available seekers: {len(available_seekers)}")
    
    if not available_seekers:
        print("[DEBUG] No available seekers found")
        return []
    
    # Cold start: if job has minimal data
    min_skills = job.skills and len(job.skills) > 0
    min_description = bool(job.description and len(job.description) > 10)
    
    if not (min_skills or min_description):
        print("[DEBUG] Using cold start approach - job has minimal data")
        # Use rule-based approach for cold start
        return rule_based_candidate_recommendation(job, available_seekers, top_n)
    
    # Try ML-based recommendation first
    try:
        print("[DEBUG] Attempting ML-based recommendation")
        
        # STRICT REQUIREMENT: Check for skill overlap first
        job_dict = as_dict_job(job)
        job_skills = job_dict.get("skills", [])
        job_requirements = job_dict.get("requirements", [])
        
        # Print detailed job info for debugging
        print(f"[DEBUG] Job ID: {getattr(job, 'id', 'unknown')}, Title: {getattr(job, 'title', 'unknown')}")
        print(f"[DEBUG] Job Skills: {job_skills}")
        print(f"[DEBUG] Job Requirements: {job_requirements}")
        print(f"[DEBUG] Job Experience Level: {job_dict.get('experience_level', 'None')}")
        print(f"[DEBUG] Job Min Experience: {job_dict.get('min_experience', 0)}")
        
        # Normalize skills for matching
        normalized_job_skills = normalize_skills(job_skills)
        
        if not normalized_job_skills:
            print("[DEBUG] Job has no skills listed, cannot match candidates")
            return []
            
        print(f"[DEBUG] Job normalized skills: {normalized_job_skills}")
        
        # Pre-filter seekers using enhanced matching functions
        filtered_seekers = []
        for seeker in available_seekers:
            seeker_dict = as_dict_job_seeker(seeker)
            seeker_skills = seeker_dict.get("skills", [])
            
            # Skip if seeker has no skills
            if not seeker_skills:
                print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has no skills listed, skipping")
                continue
                
            # Normalize seeker skills
            normalized_seeker_skills = normalize_skills(seeker_skills)
            print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} normalized skills: {normalized_seeker_skills}")
                
            # Use enhanced skill matching
            matching_skills, skill_score = get_matching_skills(normalized_seeker_skills, normalized_job_skills)
            
            if matching_skills:
                # Also check experience requirements using enhanced extraction
                seeker_exp_years = extract_experience_years(seeker_dict.get("experience", []))
                job_min_exp = job_dict.get("min_experience", 0)
                
                # Filter out seekers with significantly less experience than required
                # Allow 60% of required experience (reduced from 70% to account for data quality issues)
                if job_min_exp > 0 and seeker_exp_years < job_min_exp * 0.6:
                    print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has insufficient experience: {seeker_exp_years} vs required {job_min_exp}")
                    continue
                    
                # Check job type preferences if specified
                job_type = job_dict.get("job_type", "")
                seeker_job_types = seeker_dict.get("preferred_job_types", [])
                
                # If seeker has job type preferences and job type doesn't match, skip
                if seeker_job_types and job_type and not job_type_match(seeker_job_types, job_type):
                    print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} job type preference doesn't match")
                    continue
                    
                filtered_seekers.append(seeker)
                print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} passed pre-filtering with {len(matching_skills)} matching skills")
            else:
                print(f"[DEBUG] Seeker ID {getattr(seeker, 'id', 'unknown')} has no matching skills, skipping")
        
        print(f"[DEBUG] {len(filtered_seekers)} seekers passed all pre-filtering criteria")
        
        if not filtered_seekers:
            print("[DEBUG] No seekers met the pre-filtering criteria")
            return []
        
        # ML-based recommendation for jobs with sufficient data
        features = [extract_candidate_features(seeker, job) for seeker in filtered_seekers]
        if not features:
            print("[DEBUG] No features extracted, falling back to rule-based")
            return rule_based_candidate_recommendation(job, available_seekers, top_n)
        
        X = np.stack(features)
        scores = candidate_catboost_model.predict_proba(X)[:, 1]
        scored = list(zip(scores, filtered_seekers))
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Print top scores for debugging
        if scored:
            print(f"[DEBUG] ML top scores: {[round(score, 2) for score, _ in scored[:5]]}")
        
        # STRICT REQUIREMENT: Only return candidates with scores above threshold
        recommended = [seeker for score, seeker in scored[:top_n] if score >= score_threshold]
        
        # If no candidates meet threshold but some have reasonable scores (at least 0.15)
        if not recommended and scored and scored[0][0] >= 0.15:
            print("[DEBUG] No candidates above threshold but some reasonable scores found")
            recommended = [seeker for score, seeker in scored[:5] if score >= 0.15]
        
        # If still no recommendations, fall back to rule-based
        if not recommended:
            print("[DEBUG] ML model returned no recommendations, falling back to rule-based")
            return rule_based_candidate_recommendation(job, available_seekers, top_n)
            
        print(f"[DEBUG] Returning {len(recommended)} ML-based recommendations")
        return recommended
        
    except Exception as e:
        # If ML approach fails for any reason, fall back to rule-based
        print(f"[DEBUG] ML recommendation failed with error: {str(e)}")
        print("[DEBUG] Falling back to rule-based recommendation")
        return rule_based_candidate_recommendation(job, available_seekers, top_n)

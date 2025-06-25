# AI logic for job recommendations for job seekers
# Placeholder for actual ML model integration

import numpy as np
import os
import pickle
from typing import List, Dict, Any, Tuple
from django.conf import settings
from catboost import CatBoostClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/job_recommendation_model.cbm')
job_catboost_model = CatBoostClassifier()
job_catboost_model.load_model(MODEL_PATH)

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

def extract_job_features(seeker, job):
    """Extract features for job recommendation model"""
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

def rule_based_job_recommendation(seeker, jobs, top_n=10):
    """
    Enhanced rule-based job recommendation that doesn't rely on ML models.
    Uses direct matching on skills, education, and location with weighted scoring.
    Enforces strict matching criteria - will return empty list if no good matches.
    
    Args:
        seeker: The job seeker to find jobs for
        jobs: List of jobs to consider
        top_n: Number of jobs to return
        
    Returns:
        List of recommended jobs
    """
    from django.utils import timezone
    
    # Filter to active jobs first
    active_jobs = [job for job in jobs if job.application_deadline >= timezone.now().date()]
    jobs_to_process = active_jobs if active_jobs else jobs
    print(f"[DEBUG] Rule-based: {len(jobs_to_process)} active jobs to process")
    
    if not jobs_to_process:
        print("[DEBUG] No active jobs found")
        return []
    
    # Convert seeker to dict for feature extraction
    seeker_dict = as_dict_job_seeker(seeker)
    seeker_skills = seeker_dict.get("skills", [])
    seeker_education = seeker_dict.get("education", {})
    seeker_location = seeker_dict.get("location", "")
    seeker_job_types = seeker_dict.get("preferred_job_types", [])
    seeker_experience = seeker_dict.get("experience", [])
    
    # Get seeker's experience using enhanced extraction
    seeker_exp_years = extract_experience_years(seeker_experience)
    
    if not seeker_skills:
        print("[DEBUG] Seeker has no skills listed, cannot match jobs")
        return []
    
    # Normalize seeker skills
    normalized_seeker_skills = normalize_skills(seeker_skills)
    print(f"[DEBUG] Seeker skills (normalized): {normalized_seeker_skills}")
    
    # Score each job
    scored_jobs = []
    for job in jobs_to_process:
        job_dict = as_dict_job(job)
        job_skills = job_dict.get("skills", [])
        job_requirements = job_dict.get("requirements", [])
        job_location = job_dict.get("location", "")
        job_type = job_dict.get("job_type", "")
        job_min_exp = job_dict.get("min_experience", 0)
        
        # Skip if job has no skills
        if not job_skills:
            print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} has no skills listed, skipping")
            continue
        
        # Get matching skills using enhanced matching
        matching_skills, skills_score = get_matching_skills(seeker_skills, job_skills)
        
        # STRICT REQUIREMENT: Must have at least one matching skill
        if not matching_skills:
            print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} has no matching skills, skipping")
            continue
            
        print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} has matching skills: {matching_skills}")
        
        # Adjust skills score weight (60% weight) - most important
        skills_score = skills_score * 0.6
        
        # Education match (15% weight) using enhanced education matching
        education_score = 0.0
        if seeker_education and job_requirements:
            education_score = education_level_score(seeker_education, job_requirements) * 0.15
        
        # Location match (15% weight) using enhanced location matching
        location_score = 0.0
        if seeker_location and job_location:
            location_score = enhanced_location_match(
                seeker_location, 
                job_location,
                seeker_dict.get("willing_to_relocate", False)
            ) * 0.15
        
        # Job type match (10% weight) using enhanced job type matching
        job_type_score = 0.0
        if job_type:
            job_type_score = job_type_match(seeker_job_types, job_type) * 0.1
            
            # STRICT REQUIREMENT: If seeker has job type preferences, job must match
            if seeker_job_types and job_type_score == 0:
                print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} job type doesn't match seeker preferences")
                continue
        
        # Experience check - STRICT REQUIREMENT
        # Skip jobs requiring more experience than seeker has (allow 60% of required)
        if job_min_exp > 0 and seeker_exp_years < job_min_exp * 0.6:
            print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} requires more experience than seeker has: {job_min_exp} vs {seeker_exp_years}")
            continue
        
        # Calculate final score
        score = skills_score + education_score + location_score + job_type_score
        
        # STRICT REQUIREMENT: Must have a minimum total score
        if score < 0.3:  # Minimum 30% match required
            print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} has insufficient total score: {score:.2f}")
            continue
        
        scored_jobs.append((score, job))
    
    # Sort by score (highest first)
    scored_jobs.sort(reverse=True, key=lambda x: x[0])
    
    # Print top scores for debugging
    if scored_jobs:
        print(f"[DEBUG] Rule-based top job scores: {[round(score, 2) for score, _ in scored_jobs[:5]]}")
    else:
        print("[DEBUG] No jobs met the strict matching criteria")
    
    # Return jobs with good scores, up to top_n
    return [job for score, job in scored_jobs[:top_n]]


def get_job_recommendations_for_seeker(seeker, jobs, top_n=10, score_threshold=0.5, explain=False):
    """
    Get job recommendations for a seeker using a hybrid approach:
    1. ML model-based scoring (primary approach)
    2. Rule-based fallback if ML model fails or returns no results
    3. Cold start handling for seekers with minimal profile data
    
    Args:
        seeker: The job seeker to find jobs for
        jobs: List of jobs to consider
        top_n: Maximum number of recommendations to return
        score_threshold: Minimum score threshold for ML recommendations
        explain: Whether to include explanation of scores
        
    Returns:
        List of recommended jobs
    """
    print(f"[DEBUG] Finding jobs for seeker ID: {seeker.id}, name: {getattr(seeker, 'user', None) and seeker.user.get_full_name()}")
    print(f"[DEBUG] Total jobs to evaluate: {len(jobs)}")
    
    # Check for minimal profile data (cold start condition)
    min_skills = seeker.skills and len(seeker.skills) > 0
    min_location = bool(getattr(seeker, 'location', None))
    min_experience = seeker.experience and len(seeker.experience) > 0
    
    # Filter jobs to active ones first
    from django.utils import timezone
    active_jobs = [job for job in jobs if job.application_deadline >= timezone.now().date()]
    print(f"[DEBUG] Active jobs: {len(active_jobs)}")
    
    # If no active jobs, use all jobs
    jobs_to_process = active_jobs if active_jobs else jobs
    
    # Cold start: use rule-based for minimal profiles
    if not (min_skills or min_location or min_experience):
        print("[DEBUG] Using cold start approach - seeker has minimal profile data")
        return rule_based_job_recommendation(seeker, jobs_to_process, top_n)
    # Try ML-based recommendation
    try:
        print("[DEBUG] Attempting ML-based job recommendation")
        
        # Convert seeker to dict for feature extraction
        seeker_dict = as_dict_job_seeker(seeker)
        seeker_skills = seeker_dict.get("skills", [])
        seeker_education = seeker_dict.get("education", {})
        seeker_location = seeker_dict.get("location", "")
        seeker_job_types = seeker_dict.get("preferred_job_types", [])
        seeker_experience = seeker_dict.get("experience", [])
        
        # Print detailed seeker info for debugging
        print(f"[DEBUG] Seeker ID: {getattr(seeker, 'id', 'unknown')}")
        print(f"[DEBUG] Seeker Skills: {seeker_skills}")
        print(f"[DEBUG] Seeker Education: {seeker_education}")
        print(f"[DEBUG] Seeker Location: {seeker_location}")
        print(f"[DEBUG] Seeker Job Types: {seeker_job_types}")
        
        # Get seeker's experience using enhanced extraction
        seeker_exp_years = extract_experience_years(seeker_experience)
        print(f"[DEBUG] Seeker Experience Years: {seeker_exp_years}")
        
        if not seeker_skills:
            print("[DEBUG] Seeker has no skills listed, cannot match jobs")
            return []
        
        # Normalize seeker skills
        normalized_seeker_skills = normalize_skills(seeker_skills)
        print(f"[DEBUG] Seeker skills (normalized): {normalized_seeker_skills}")
        
        # Pre-filter jobs using enhanced matching functions
        filtered_jobs = []
        for job in jobs_to_process:
            job_dict = as_dict_job(job)
            job_skills = job_dict.get("skills", [])
            job_requirements = job_dict.get("requirements", [])
            
            # Print detailed job info for debugging
            print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')}, Title: {getattr(job, 'title', 'unknown')}")
            print(f"[DEBUG] Job Skills: {job_skills}")
            print(f"[DEBUG] Job Requirements: {job_requirements}")
            print(f"[DEBUG] Job Experience Level: {job_dict.get('experience_level', 'None')}")
            print(f"[DEBUG] Job Min Experience: {job_dict.get('min_experience', 0)}")
            
            # Skip if job has no skills
            if not job_skills:
                print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} has no skills listed, skipping")
                continue
                
            # Normalize job skills
            normalized_job_skills = normalize_skills(job_skills)
            print(f"[DEBUG] Job normalized skills: {normalized_job_skills}")
                
            # Use enhanced skill matching
            matching_skills, skill_score = get_matching_skills(normalized_seeker_skills, normalized_job_skills)
            
            if matching_skills:
                filtered_jobs.append(job)
                print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} has matching skills: {matching_skills}")
            else:
                print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} has no matching skills, skipping")
        
        print(f"[DEBUG] {len(filtered_jobs)} jobs have at least one matching skill")
        
        if not filtered_jobs:
            print("[DEBUG] No jobs with matching skills found")
            return []
            
        # Pre-filter jobs by experience requirements using enhanced experience extraction
        experience_filtered_jobs = []
        for job in filtered_jobs:
            job_dict = as_dict_job(job)
            job_min_exp = job_dict.get("min_experience", 0)
            
            # Allow 60% of required experience (reduced from 80% to account for data quality issues)
            if job_min_exp == 0 or seeker_exp_years >= job_min_exp * 0.6:
                # Also check job type preferences if specified
                job_type = job_dict.get("job_type", "")
                
                # If seeker has job type preferences and job type doesn't match, skip
                if seeker_job_types and job_type and not job_type_match(seeker_job_types, job_type):
                    print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} job type doesn't match seeker preferences")
                    continue
                    
                experience_filtered_jobs.append(job)
            else:
                print(f"[DEBUG] Job ID {getattr(job, 'id', 'unknown')} requires more experience than seeker has: {job_min_exp} vs {seeker_exp_years}")
        
        print(f"[DEBUG] {len(experience_filtered_jobs)} jobs passed all pre-filtering criteria")
        
        if not experience_filtered_jobs:
            print("[DEBUG] No jobs met the pre-filtering criteria")
            return []
        
        # ML-based recommendation for filtered jobs
        features_list = [extract_job_features(seeker, job) for job in experience_filtered_jobs]
        if not features_list:
            print("[DEBUG] No features extracted, falling back to rule-based")
            return rule_based_job_recommendation(seeker, jobs_to_process, top_n)
        
        X = np.stack(features_list)
        scores = job_catboost_model.predict_proba(X)[:, 1]
        scored = list(zip(scores, experience_filtered_jobs))
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Print scores for debugging
        if scored:
            print(f"[DEBUG] ML top job scores: {[round(score, 2) for score, _ in scored[:5]]}")
        
        # STRICT REQUIREMENT: Only return jobs with scores above threshold
        recommended = [job for score, job in scored[:top_n] if score >= score_threshold]
        
        # If no jobs meet threshold but some have reasonable scores (at least 0.3)
        if not recommended and scored and scored[0][0] >= 0.3:
            print("[DEBUG] No jobs above threshold but some reasonable scores found")
            recommended = [job for score, job in scored[:5] if score >= 0.3]
        
        # If still no recommendations, fall back to rule-based
        if not recommended:
            print("[DEBUG] ML model returned no recommendations, falling back to rule-based")
            return rule_based_job_recommendation(seeker, jobs_to_process, top_n)
            
        print(f"[DEBUG] Returning {len(recommended)} ML-based job recommendations")
        return recommended
        
    except Exception as e:
        # If ML approach fails for any reason, fall back to rule-based
        print(f"[DEBUG] ML job recommendation failed with error: {str(e)}")
        print("[DEBUG] Falling back to rule-based job recommendation")
        return rule_based_job_recommendation(seeker, jobs_to_process, top_n)

    if explain:
        return [
            {
                "job": job,
                "score": float(score),
                "features": dict(zip(FEATURE_ORDER, extract_job_features(seeker, job))),
            }
            for score, job in scored[:top_n] if score >= 0.3
        ]
    else:
        return recommended

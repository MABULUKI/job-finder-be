# AI logic for job recommendations for job seekers
# Placeholder for actual ML model integration

import numpy as np
import os
from catboost import CatBoostClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/job_catboost_model.cbm')
catboost_model = CatBoostClassifier()
catboost_model.load_model(MODEL_PATH)

def extract_features(seeker, job):
    seeker_skills = set(seeker.skills or [])
    job_skills = set(job.requirements or [])
    skill_match_score = len(seeker_skills & job_skills) / max(1, len(job_skills))
    salary_match = int((job.salary_min or 0) >= (seeker.salary_expectation or 0))
    location_match = int((job.location or '').lower() == (seeker.location or '').lower())
    seeker_exp = sum([e.get('years', 0) for e in (seeker.experience or [])])
    job_exp_level = getattr(job, 'experience_level', 'ENTRY')
    experience_match = int(seeker_exp >= (2 if job_exp_level == 'MID' else 5 if job_exp_level == 'SENIOR' else 0))
    return np.array([skill_match_score, salary_match, location_match, experience_match])

def get_job_recommendations_for_seeker(seeker, jobs, top_n=10, score_threshold=0.5):
    # Cold start: no or minimal profile data
    min_skills = seeker.skills and len(seeker.skills) > 0
    min_location = bool(getattr(seeker, 'location', None))
    min_experience = seeker.experience and len(seeker.experience) > 0
    # If no skills, no experience, no location: fallback
    if not (min_skills or min_location or min_experience):
        # Fallback: score jobs by popularity, salary, city, job type, and random minimal skill overlap
        jobs = list(jobs)
        # Popularity: number of applications
        job_app_counts = {job.id: getattr(job, 'application_set', []).count() if hasattr(job, 'application_set') else 0 for job in jobs}
        def fallback_score(job):
            score = 0
            # Popularity
            score += job_app_counts.get(job.id, 0) * 2
            # Salary
            score += (job.salary_min or 0) / 1e6
            # City: prefer Dar es Salaam, Dodoma, Arusha
            if (job.location or '').lower() in ['dar es salaam', 'dodoma', 'arusha']:
                score += 2
            # Job type: prefer full-time
            if getattr(job, 'job_type', None) == 'FULL_TIME':
                score += 1
            # Minimal skill overlap: random
            score += np.random.rand()
            return score
        ranked = sorted(jobs, key=fallback_score, reverse=True)
        return ranked[:top_n]
    # Normal ML-based recommendation
    features = [extract_features(seeker, job) for job in jobs]
    if not features:
        return []
    X = np.stack(features)
    scores = catboost_model.predict_proba(X)[:, 1]
    ranked = sorted(zip(jobs, scores), key=lambda x: x[1], reverse=True)
    filtered = [job for job, score in ranked if score > score_threshold]
    if filtered:
        return filtered[:top_n]
    # If nothing passes threshold, return top scoring job(s)
    return [job for job, _ in ranked[:max(1, top_n)]]

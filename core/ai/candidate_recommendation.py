# AI logic for candidate recommendations for recruiters
# Placeholder for actual ML model integration

import numpy as np
import os
from catboost import CatBoostClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/candidate_catboost_model.cbm')
catboost_model = CatBoostClassifier()
catboost_model.load_model(MODEL_PATH)


def extract_candidate_features(job, seeker):
    seeker_skills = set(seeker.skills or [])
    job_skills = set(job.requirements or [])
    skill_match_score = len(seeker_skills & job_skills) / max(1, len(job_skills))
    salary_match = int((job.salary_min or 0) >= (seeker.salary_expectation or 0))
    location_match = int((job.location or '').lower() == (seeker.location or '').lower())
    seeker_exp = sum([e.get('years', 0) for e in (seeker.experience or [])])
    job_exp_level = getattr(job, 'experience_level', 'ENTRY')
    experience_match = int(seeker_exp >= (2 if job_exp_level == 'MID' else 5 if job_exp_level == 'SENIOR' else 0))
    return np.array([skill_match_score, salary_match, location_match, experience_match])


def get_candidate_recommendations_for_job(job, seekers, top_n=10):
    features = [extract_candidate_features(job, seeker) for seeker in seekers]
    if not features:
        return []
    X = np.stack(features)
    scores = catboost_model.predict_proba(X)[:, 1]
    ranked = sorted(zip(seekers, scores), key=lambda x: x[1], reverse=True)
    return [seeker for seeker, _ in ranked[:top_n]]

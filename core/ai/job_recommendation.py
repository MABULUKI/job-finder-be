# AI logic for job recommendations for job seekers
# Placeholder for actual ML model integration

import numpy as np
import os
from catboost import CatBoostClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/job_recommendation_model.cbm')
job_catboost_model = CatBoostClassifier()
job_catboost_model.load_model(MODEL_PATH)

from core.ai.feature_extraction import (
    extract_features,
    jaccard_similarity,
    education_match,
    location_match,
    preferred_job_type_match,
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
    features = extract_features(as_dict_job_seeker(seeker), as_dict_job(job))
    return [features.get(f, 0) for f in FEATURE_ORDER]

def get_job_recommendations_for_seeker(seeker, jobs, top_n=10, score_threshold=0.5, explain=False):
    # Cold start: no or minimal profile data
    min_skills = seeker.skills and len(seeker.skills) > 0
    min_location = bool(getattr(seeker, 'location', None))
    min_experience = seeker.experience and len(seeker.experience) > 0
    if not (min_skills or min_location or min_experience):
        # ML-consistent cold start: score jobs by skills, education, location, preferred job type
        def cold_start_score(job):
            seeker_dict = as_dict_job_seeker(seeker)
            job_dict = as_dict_job(job)
            score = 0.0
            score += jaccard_similarity(seeker_dict["skills"], job_dict["skills"]) * 0.5
            score += education_match(seeker_dict["education"], job_dict["education"]) * 0.2
            score += location_match(seeker_dict["location"], job_dict["location"], seeker_dict.get("willing_to_relocate", False)) * 0.2
            score += preferred_job_type_match(seeker_dict["preferred_job_types"], job_dict["job_type"]) * 0.1
            return score
        scored = [(cold_start_score(job), job) for job in jobs]
        scored.sort(reverse=True, key=lambda x: x[0])
        return [job for score, job in scored[:top_n] if score > 0]
    # ML-based recommendation
    features_list = [extract_job_features(seeker, job) for job in jobs]
    if not features_list:
        return []
    import numpy as np
    X = np.array(features_list)
    scores = job_catboost_model.predict_proba(X)[:, 1]
    ranked = sorted(zip(jobs, scores, features_list), key=lambda x: x[1], reverse=True)
    filtered = [r for r in ranked if r[1] > score_threshold]
    top = filtered[:top_n] if filtered else ranked[:max(1, top_n)]
    if explain:
        return [
            {
                "job": job,
                "score": float(score),
                "features": dict(zip(FEATURE_ORDER, feats)),
            }
            for job, score, feats in top
        ]
    else:
        return [job for job, _, _ in top]

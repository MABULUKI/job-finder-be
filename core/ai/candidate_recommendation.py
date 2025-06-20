# AI logic for candidate recommendations for recruiters
# Placeholder for actual ML model integration

import numpy as np
import os
from catboost import CatBoostClassifier

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models/candidate_recommendation_model.cbm')
candidate_catboost_model = CatBoostClassifier()
candidate_catboost_model.load_model(MODEL_PATH)


from core.ai.feature_extraction import extract_features

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
    features = extract_features(as_dict_job_seeker(seeker), as_dict_job(job))
    return [features.get(f, 0) for f in FEATURE_ORDER]


def get_candidate_recommendations_for_job(job, seekers, top_n=10, score_threshold=0.25, explain=False):
    # Input: job, list of seeker profiles
    # Output: ranked list of seekers (optionally with score breakdown)
    features = [extract_candidate_features(seeker, job) for seeker in seekers]
    if not features:
        return []
    X = np.stack(features)
    scores = candidate_catboost_model.predict_proba(X)[:, 1]
    scored = list(zip(scores, seekers))
    scored.sort(reverse=True, key=lambda x: x[0])
    recommended = [seeker for score, seeker in scored[:top_n] if score >= score_threshold]
    return recommended

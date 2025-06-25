"""
Feature extraction helpers for job and candidate recommendations.
Imports logic from ml_training/feature_extraction.py for DRY code.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ml_training')))
from feature_extraction import *

# Adapter: ORM -> dict for ML feature extraction

def as_dict_job_seeker(seeker):
    return {
        "skills": getattr(seeker, "skills", []),
        "education": getattr(seeker, "education", []),
        "location": getattr(seeker, "location", None),
        "preferred_job_types": getattr(seeker, "preferred_job_types", []),
        "experience": getattr(seeker, "experience", []),
        "salary_expectation": getattr(seeker, "salary_expectation", 0),
        "seeker_rating": getattr(seeker, "seeker_rating", 0),
        "is_available": getattr(seeker, "is_available", True),
        "willing_to_relocate": getattr(seeker, "willing_to_relocate", False),
    }

def as_dict_job(job):
    return {
        "skills": getattr(job, "skills", []),  # Fixed: use skills field instead of requirements
        "requirements": getattr(job, "requirements", []),  # Added: keep requirements separate
        "education": getattr(job, "education", []),
        "location": getattr(job, "location", None),
        "job_type": getattr(job, "job_type", None),
        "salary_min": getattr(job, "salary_min", 0),
        "salary_max": getattr(job, "salary_max", 0),
        "min_experience": getattr(job, "min_experience", 0),  # Added: explicit min_experience
        "experience_level": getattr(job, "experience_level", None),
        "next_step": getattr(job, "next_step", None),
    }

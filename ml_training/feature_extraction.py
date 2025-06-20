"""
Feature extraction for job recommendation and candidate recommendation.
- Handles both model and cold-start logic.
- PEP8, type hints, modular, robust.
"""
from typing import Dict, Any, List, Optional, Set
import numpy as np

def jaccard_similarity(list1: List[str], list2: List[str]) -> float:
    set1, set2 = set(list1), set(list2)
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def skills_overlap(list1: List[str], list2: List[str]) -> int:
    return len(set(list1) & set(list2))

def education_match(edu1: List[Dict[str, Any]], edu2: List[Dict[str, Any]]) -> float:
    # Match on level and field for any entry
    for e1 in edu1:
        for e2 in edu2:
            if (
                e1.get("level", "").lower() == e2.get("level", "").lower()
                and e1.get("field", "").lower() == e2.get("field", "").lower()
            ):
                return 1.0
    return 0.0

def experience_years(exp: List[Dict[str, Any]]) -> int:
    total = 0
    for e in exp:
        total += int(e.get("years", 0))
    return total

def preferred_job_type_match(seeker_types: List[str], job_type: str) -> int:
    return int(job_type in seeker_types)

def location_match(seeker_loc: str, job_loc: str, willing_to_relocate: bool) -> int:
    if seeker_loc.lower() == job_loc.lower():
        return 1
    if willing_to_relocate:
        return 1
    return 0

def salary_within_range(seeker_salary: Optional[int], job_salary: Optional[int]) -> int:
    if seeker_salary is None or job_salary is None:
        return 0
    return int(job_salary >= seeker_salary)

def extract_features(seeker: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts features for (seeker, job) pair."""
    features = {}
    features["skills_jaccard"] = jaccard_similarity(seeker["skills"], job["skills"])
    features["skills_overlap"] = skills_overlap(seeker["skills"], job["skills"])
    features["education_match"] = education_match(seeker["education"], job["education"])
    features["experience_years"] = experience_years(seeker["experience"])
    features["job_experience_required"] = job.get("min_experience", 0)
    features["experience_gap"] = (
        features["experience_years"] - features["job_experience_required"]
    )
    features["preferred_job_type_match"] = preferred_job_type_match(
        seeker["preferred_job_types"], job["job_type"]
    )
    features["location_match"] = location_match(
        seeker["location"], job["location"], seeker.get("willing_to_relocate", False)
    )
    features["salary_within_range"] = salary_within_range(
        seeker.get("salary_expectation"), job.get("salary_offered")
    )
    features["seeker_rating"] = seeker.get("average_rating", 0)
    features["is_available"] = int(seeker.get("is_available", True))
    return features

def cold_start_job_recommendation(seeker: Dict[str, Any], jobs: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """Recommend jobs to a new seeker based on skills/education/location."""
    scored = []
    for job in jobs:
        score = 0.0
        score += jaccard_similarity(seeker["skills"], job["skills"]) * 0.5
        score += education_match(seeker["education"], job["education"]) * 0.2
        score += location_match(seeker["location"], job["location"], seeker.get("willing_to_relocate", False)) * 0.2
        score += preferred_job_type_match(seeker["preferred_job_types"], job["job_type"]) * 0.1
        scored.append((score, job))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [job for score, job in scored[:top_n] if score > 0]

def cold_start_candidate_recommendation(job: Dict[str, Any], seekers: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """Recommend seekers to a new job based on skills/education/location/availability."""
    scored = []
    for seeker in seekers:
        if not seeker.get("is_available", True):
            continue
        score = 0.0
        score += jaccard_similarity(seeker["skills"], job["skills"]) * 0.5
        score += education_match(seeker["education"], job["education"]) * 0.2
        score += location_match(seeker["location"], job["location"], seeker.get("willing_to_relocate", False)) * 0.2
        score += preferred_job_type_match(seeker["preferred_job_types"], job["job_type"]) * 0.1
        scored.append((score, seeker))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [seeker for score, seeker in scored[:top_n] if score > 0]

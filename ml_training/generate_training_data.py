"""
Generate realistic, clean, non-repetitive training data for job and candidate recommendation models.
- Skills include both white-collar and blue-collar (e.g., plumbing, cleaning, etc.)
- Education includes none, secondary, vocational, university, etc.
- No duplicate (seeker, job) rows, realistic distributions.
"""
import random
import csv
from typing import List, Dict, Any

SKILLS = [
    "plumbing", "cleaning", "teaching", "accounting", "software development", "carpentry", "driving", "nursing",
    "security", "sales", "customer service", "mechanic", "cooking", "gardening", "data entry", "marketing",
    "graphic design", "tailoring", "electrician", "construction", "barber", "hairdressing", "waiter", "baking"
]

EDUCATION_LEVELS = [
    {"level": "none", "field": "none"},
    {"level": "secondary", "field": "general"},
    {"level": "vocational", "field": "plumbing"},
    {"level": "vocational", "field": "mechanic"},
    {"level": "diploma", "field": "business"},
    {"level": "diploma", "field": "ict"},
    {"level": "bachelor", "field": "education"},
    {"level": "bachelor", "field": "engineering"},
    {"level": "bachelor", "field": "accounting"},
    {"level": "master", "field": "ict"},
    {"level": "master", "field": "business"},
]

JOB_TYPES = ["full-time", "part-time", "contract", "temporary"]
LOCATIONS = ["Dar es Salaam", "Arusha", "Mwanza", "Mbeya", "Dodoma", "Tanga", "Morogoro"]

# Helper for unique pairs
def unique_pairs(seekers, jobs):
    seen = set()
    for seeker in seekers:
        for job in jobs:
            key = (seeker["id"], job["id"])
            if key not in seen:
                seen.add(key)
                yield seeker, job

def generate_seekers(n: int) -> List[Dict[str, Any]]:
    seekers = []
    for i in range(n):
        skills = random.sample(SKILLS, k=random.randint(1, 5))
        education = [random.choice(EDUCATION_LEVELS)]
        experience = [{"role": random.choice(skills), "years": random.randint(1, 7)} for _ in range(random.randint(1, 3))]
        preferred_job_types = random.sample(JOB_TYPES, k=random.randint(1, 2))
        seeker = {
            "id": i + 1,
            "skills": skills,
            "education": education,
            "experience": experience,
            "preferred_job_types": preferred_job_types,
            "salary_expectation": random.randint(150000, 2000000),
            "location": random.choice(LOCATIONS),
            "willing_to_relocate": random.choice([True, False]),
            "is_available": random.choice([True, True, False]),
            "average_rating": round(random.uniform(2.5, 5.0), 2),
        }
        seekers.append(seeker)
    return seekers

def generate_jobs(n: int) -> List[Dict[str, Any]]:
    jobs = []
    for i in range(n):
        skills = random.sample(SKILLS, k=random.randint(1, 5))
        education = [random.choice(EDUCATION_LEVELS)]
        job = {
            "id": i + 1,
            "skills": skills,
            "education": education,
            "job_type": random.choice(JOB_TYPES),
            "location": random.choice(LOCATIONS),
            "salary_offered": random.randint(200000, 3000000),
            "min_experience": random.randint(0, 5),
        }
        jobs.append(job)
    return jobs

def label_pair(seeker: Dict[str, Any], job: Dict[str, Any]) -> int:
    # Positive label if skills overlap, education match, location match or willing to relocate, and salary within range
    from feature_extraction import jaccard_similarity, education_match, location_match, salary_within_range
    if (
        jaccard_similarity(seeker["skills"], job["skills"]) > 0.3
        and education_match(seeker["education"], job["education"]) > 0
        and location_match(seeker["location"], job["location"], seeker["willing_to_relocate"]) > 0
        and salary_within_range(seeker["salary_expectation"], job["salary_offered"]) > 0
    ):
        return 1
    return 0

def write_training_csv_balanced(seekers, jobs, out_csv, positives_target=5000, negatives_target=5000):
    from feature_extraction import extract_features
    seen = set()
    positives = []
    negatives = []
    for seeker, job in unique_pairs(seekers, jobs):
        features = extract_features(seeker, job)
        label = label_pair(seeker, job)
        key = tuple(features.values())
        if key in seen:
            continue
        seen.add(key)
        if label == 1 and len(positives) < positives_target:
            positives.append(list(features.values()) + [label])
        elif label == 0 and len(negatives) < negatives_target:
            negatives.append(list(features.values()) + [label])
        if len(positives) >= positives_target and len(negatives) >= negatives_target:
            break
    # Shuffle and write
    import random
    all_rows = positives + negatives
    random.shuffle(all_rows)
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        header = list(extract_features(seekers[0], jobs[0]).keys()) + ["label"]
        writer.writerow(header)
        for row in all_rows:
            writer.writerow(row)

def main():
    seekers = generate_seekers(800)
    jobs = generate_jobs(400)
    write_training_csv_balanced(seekers, jobs, "../ml_training/data/job_recommendation_training.csv", positives_target=5000, negatives_target=5000)

if __name__ == "__main__":
    main()

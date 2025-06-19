import csv
import random
import pandas as pd

# Load seekers and jobs
seekers = pd.read_csv('seekers.csv').to_dict('records')
jobs = pd.read_csv('jobs.csv').to_dict('records')

# Generate candidate recommendations for jobs
def generate_candidate_rows(seekers, jobs):
    rows = []
    for job in jobs:
        for seeker in random.sample(seekers, random.randint(2, 10)):
            seeker_skills = set(seeker['skills'].split('|'))
            job_skills = set(job['requirements'].split('|'))
            skill_match = len(seeker_skills & job_skills) / max(1, len(job_skills))
            salary_match = (job['salary_min'] >= seeker['salary_expectation'])
            exp_map = {'ENTRY': 0, 'MID': 2, 'SENIOR': 5}
            experience_match = seeker['experience_years'] >= exp_map.get(job['experience_level'], 0)
            label = 1 if skill_match > 0.5 and salary_match and experience_match else 0
            rows.append({
                'job_id': job['job_id'],
                'seeker_id': seeker['seeker_id'],
                'job_skills': job['requirements'],
                'seeker_skills': seeker['skills'],
                'job_experience_level': job['experience_level'],
                'seeker_experience_years': seeker['experience_years'],
                'job_location': job['location'],
                'seeker_location': seeker['location'],
                'job_salary_min': job['salary_min'],
                'seeker_salary_expectation': seeker['salary_expectation'],
                'selected': label
            })
    return rows

def write_csv(filename, rows, fieldnames):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    rows = generate_candidate_rows(seekers, jobs)
    write_csv('candidate_recommendation_dataset.csv', rows, list(rows[0].keys()))

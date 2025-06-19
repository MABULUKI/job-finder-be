import csv
import random
from faker import Faker

fake = Faker()

# Tanzanian context
TZ_CITIES = [
    "Dar es Salaam", "Dodoma", "Arusha", "Mwanza", "Mbeya", "Morogoro", "Tanga", "Zanzibar", "Kilimanjaro", "Moshi"
]
TZ_UNIVERSITIES = [
    "University of Dar es Salaam", "Ardhi University", "Muhimbili University", "Sokoine University", "University of Dodoma", "Nelson Mandela Institute", "Mzumbe University", "St. Augustine University"
]
INDUSTRIES = [
    "ICT", "Healthcare", "Education", "Finance", "Agriculture", "Tourism", "Construction", "Energy", "Transport"
]
SKILL_MAP = {
    "ICT": ["Python", "Django", "SQL", "Networking", "Linux", "Cloud", "React", "Flutter", "Android"],
    "Healthcare": ["Nursing", "Clinical Research", "Patient Care", "Lab Work", "Public Health"],
    "Education": ["Teaching", "Curriculum Design", "eLearning", "Counseling", "Special Needs"],
    "Finance": ["Accounting", "Auditing", "Excel", "Financial Analysis", "Tax"],
    "Agriculture": ["Crop Science", "Irrigation", "Livestock", "Agribusiness", "Soil Science"],
    "Tourism": ["Tour Guiding", "Hotel Management", "Travel Planning", "Customer Service", "Event Planning"],
    "Construction": ["Civil Engineering", "Site Management", "AutoCAD", "Surveying", "Safety Compliance"],
    "Energy": ["Electrical Engineering", "Renewables", "Grid Management", "Maintenance", "Energy Auditing"],
    "Transport": ["Logistics", "Fleet Management", "Driving", "Dispatch", "Route Planning"]
}
ALL_SKILLS = sorted({s for v in SKILL_MAP.values() for s in v})
EDUCATION_LEVELS = ["Certificate", "Diploma", "Bachelor", "Master", "PhD"]
EXPERIENCE_LEVELS = ["ENTRY", "MID", "SENIOR"]

# Generate seekers
def generate_seekers(n=1000):
    seekers = []
    for _ in range(n):
        industry = random.choice(INDUSTRIES)
        # Add more diversity and noise to skills
        core_skills = random.sample(SKILL_MAP[industry], min(3, len(SKILL_MAP[industry])))
        noise_skills = random.sample([s for s in ALL_SKILLS if s not in core_skills], random.randint(0, 3))
        skills = list(set(core_skills + noise_skills))
        # Add more realistic education and location variety
        education = f"{random.choices(EDUCATION_LEVELS, weights=[0.2,0.3,0.35,0.1,0.05])[0]} - {random.choice(TZ_UNIVERSITIES)}"
        city = random.choice(TZ_CITIES)
        experience = random.randint(0, 15)
        salary = random.randint(3000000, 18000000)
        seekers.append({
            "seeker_id": fake.uuid4(),
            "name": fake.name(),
            "skills": "|".join(skills),
            "industry": industry,
            "education": education,
            "location": city,
            "experience_years": experience,
            "salary_expectation": salary
        })
    return seekers

# Generate recruiters
def generate_recruiters(n=100):
    recruiters = []
    for _ in range(n):
        industry = random.choice(INDUSTRIES)
        company_size = random.choice(["1-10", "11-50", "51-200", "201-1000", "1000+"])
        recruiters.append({
            "recruiter_id": fake.uuid4(),
            "name": fake.company(),
            "industry": industry,
            "company_size": company_size,
            "location": random.choice(TZ_CITIES)
        })
    return recruiters

# Generate jobs
def generate_jobs(recruiters, n=1000):
    jobs = []
    for _ in range(n):
        recruiter = random.choice(recruiters)
        industry = recruiter["industry"]
        # Add more diversity and noise to job requirements
        core_skills = random.sample(SKILL_MAP[industry], min(3, len(SKILL_MAP[industry])))
        noise_skills = random.sample([s for s in ALL_SKILLS if s not in core_skills], random.randint(0, 3))
        skills = list(set(core_skills + noise_skills))
        exp_level = random.choices(EXPERIENCE_LEVELS, weights=[0.5, 0.35, 0.15])[0]
        salary_min = random.randint(3000000, 15000000)
        salary_max = salary_min + random.randint(500000, 5000000)
        jobs.append({
            "job_id": fake.uuid4(),
            "title": fake.job(),
            "recruiter_id": recruiter["recruiter_id"],
            "industry": industry,
            "requirements": "|".join(skills),
            "location": recruiter["location"],
            "experience_level": exp_level,
            "salary_min": salary_min,
            "salary_max": salary_max
        })
    return jobs

# Generate applications (for job recommendation training)
def generate_applications(seekers, jobs):
    rows = []
    for seeker in seekers:
        for job in random.sample(jobs, random.randint(2, 10)):
            # Label: 1 if skills overlap and salary meets expectation, else 0
            seeker_skills = set(seeker["skills"].split("|"))
            job_skills = set(job["requirements"].split("|"))
            skill_match = len(seeker_skills & job_skills) / max(1, len(job_skills))
            salary_match = job["salary_min"] >= seeker["salary_expectation"]
            label = 1 if skill_match > 0.5 and salary_match else 0
            rows.append({
                "seeker_id": seeker["seeker_id"],
                "job_id": job["job_id"],
                "seeker_skills": seeker["skills"],
                "job_skills": job["requirements"],
                "seeker_experience_years": seeker["experience_years"],
                "job_experience_level": job["experience_level"],
                "seeker_location": seeker["location"],
                "job_location": job["location"],
                "seeker_salary_expectation": seeker["salary_expectation"],
                "job_salary_min": job["salary_min"],
                "applied": label
            })
    return rows

# Write CSVs
def write_csv(filename, rows, fieldnames):
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    seekers = generate_seekers(1000)
    recruiters = generate_recruiters(100)
    jobs = generate_jobs(recruiters, 1000)
    # Job recommendation dataset
    job_applications = generate_applications(seekers, jobs)
    write_csv("job_recommendation_dataset.csv", job_applications, list(job_applications[0].keys()))
    # Save seekers and jobs for candidate recommendation
    write_csv("seekers.csv", seekers, list(seekers[0].keys()))
    write_csv("jobs.csv", jobs, list(jobs[0].keys()))

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_portal_backend.settings')
django.setup()

# Import models
from core.models import Job
from authentication.models import JobSeekerProfile

def print_job_details():
    print("\n===== JOB EXAMPLES =====")
    jobs = Job.objects.all()[:5]  # Get up to 5 jobs
    
    if not jobs:
        print("No jobs found in database")
        return
    
    for i, job in enumerate(jobs, 1):
        print(f"\nJob #{i} (ID: {job.id}):")
        print(f"  Title: {job.title}")
        print(f"  Job Type: {job.job_type}")
        print(f"  Experience Level: {job.experience_level}")
        print(f"  Location: {job.location}")
        print(f"  Remote: {job.is_remote}")
        print(f"  Skills: {job.skills}")
        print(f"  Requirements: {job.requirements}")
        print(f"  Salary Range: {job.salary_min} - {job.salary_max}")
        print(f"  Posted: {job.posted_at}")
        print(f"  Deadline: {job.application_deadline}")

def print_seeker_details():
    print("\n===== JOB SEEKER EXAMPLES =====")
    seekers = JobSeekerProfile.objects.all()[:5]  # Get up to 5 seekers
    
    if not seekers:
        print("No job seekers found in database")
        return
    
    for i, seeker in enumerate(seekers, 1):
        print(f"\nSeeker #{i} (ID: {seeker.id}):")
        print(f"  Name: {seeker.full_name}")
        print(f"  Available: {seeker.is_available}")
        print(f"  Location: {seeker.location}")
        print(f"  Willing to Relocate: {seeker.willing_to_relocate}")
        print(f"  Skills: {seeker.skills}")
        
        # Print education details
        print("  Education:")
        for edu in seeker.education:
            try:
                print(f"    - {edu.get('level', 'N/A')}: {edu.get('type', 'N/A')} in {edu.get('field', 'N/A')} from {edu.get('institution', 'N/A')} ({edu.get('year', 'N/A')})")
            except Exception as e:
                print(f"    - Error parsing education: {edu}")
        
        # Print experience details
        print("  Experience:")
        for exp in seeker.experience:
            try:
                print(f"    - {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('duration', 'N/A')})")
                if 'years' in exp:
                    print(f"      Years: {exp.get('years', 'N/A')}")
            except Exception as e:
                print(f"    - Error parsing experience: {exp}")
        
        print(f"  Preferred Job Types: {seeker.preferred_job_types}")
        print(f"  Salary Expectation: {seeker.salary_expectation}")

if __name__ == "__main__":
    print("Examining database records...")
    print_job_details()
    print_seeker_details()
    print("\nDone.")

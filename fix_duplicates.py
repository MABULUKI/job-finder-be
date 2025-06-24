"""
Script to identify and remove duplicate job applications before applying migrations.
This script will:
1. Find all duplicate applications (same job and seeker)
2. Keep the oldest application for each job-seeker pair
3. Delete the duplicates
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_portal_backend.settings')
django.setup()

from core.models import Application
from django.db.models import Count
from django.db import transaction

def fix_duplicate_applications():
    print("Checking for duplicate applications...")
    
    # Find all job-seeker pairs with more than one application
    duplicates = Application.objects.values('job', 'seeker').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    duplicate_count = len(duplicates)
    print(f"Found {duplicate_count} job-seeker pairs with duplicate applications")
    
    if duplicate_count == 0:
        print("No duplicates found. Database is clean.")
        return
    
    # Process each duplicate set
    with transaction.atomic():
        for dup in duplicates:
            job_id = dup['job']
            seeker_id = dup['seeker']
            
            # Get all applications for this job-seeker pair, ordered by application date
            applications = Application.objects.filter(
                job_id=job_id, 
                seeker_id=seeker_id
            ).order_by('applied_at')
            
            # Keep the oldest application, delete the rest
            oldest_app = applications.first()
            duplicate_apps = applications.exclude(id=oldest_app.id)
            
            print(f"Job ID: {job_id}, Seeker ID: {seeker_id}")
            print(f"  Keeping application ID: {oldest_app.id} (applied: {oldest_app.applied_at})")
            print(f"  Deleting {duplicate_apps.count()} duplicate applications")
            
            # Delete the duplicates
            duplicate_apps.delete()
    
    print("\nDuplicate cleanup complete!")
    print("You can now run 'python manage.py migrate' to apply the unique constraint.")

if __name__ == "__main__":
    fix_duplicate_applications()

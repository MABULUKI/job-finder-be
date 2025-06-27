from django.db import models
from django.contrib.auth.models import AbstractUser

COMPANY_SIZE_CHOICES = [
    ('1-10', '1-10 employees'),
    ('11-50', '11-50 employees'),
    ('51-200', '51-200 employees'),
    ('201-500', '201-500 employees'),
    ('501-1000', '501-1000 employees'),
    ('1000+', '1000+ employees'),
]

JOB_TYPE_CHOICES = [
    ('FULL_TIME', 'Full-time'),
    ('PART_TIME', 'Part-time'),
    ('CONTRACT', 'Contract'),
    ('INTERNSHIP', 'Internship'),
    ('TEMPORARY', 'Temporary'),
]

INDUSTRY_CHOICES = [
    ('IT', 'Information Technology'),
    ('FINANCE', 'Finance'),
    ('HEALTHCARE', 'Healthcare'),
    # Add more as needed
]

from django.conf import settings

class User(AbstractUser):
    # Use email as the unique identifier for authentication
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email or self.username

class RecruiterProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recruiter_profile')
    company_name = models.CharField(max_length=100)
    company_description = models.TextField(blank=True)
    industry = models.CharField(max_length=50, blank=True)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='recruiter_logos/', blank=True, null=True)
    profile_updated = models.BooleanField(default=False)

    def __str__(self):
        return f"RecruiterProfile({self.user.email})"

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seeker_profile')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    linkedin = models.URLField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    skills = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    preferred_job_types = models.JSONField(default=list, blank=True)
    salary_expectation = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    willing_to_relocate = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    profile_updated = models.BooleanField(default=False)

    # Aggregate rating for seeker using the unified feedback system
    @property
    def average_rating(self):
        ratings = self.all_feedbacks.all().values_list('rating', flat=True)
        if not ratings:
            return None
        # Calculate average but ensure it doesn't exceed 5.0
        avg = sum(ratings) / len(ratings)
        return min(round(avg, 2), 5.0)

    @property
    def feedback_count(self):
        return self.all_feedbacks.count()
        
    @property
    def application_feedbacks(self):
        """Get only feedbacks related to applications"""
        return self.all_feedbacks.filter(feedback_type='APPLICATION')
    
    @property
    def profile_feedbacks(self):
        """Get only general profile feedbacks"""
        return self.all_feedbacks.filter(feedback_type='PROFILE')

    def __str__(self):
        return f"JobSeekerProfile({self.user.email})"

# SeekerFeedback model has been moved to core.models.FeedbackRating
# This provides a unified feedback system for both application-specific and general profile feedback

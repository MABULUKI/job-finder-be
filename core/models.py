from django.db import models

# Recruiter and JobSeeker models have been moved to the authentication app.

INDUSTRY_CHOICES = [
    ('IT', 'Information Technology'),
    ('FINANCE', 'Finance'),
    ('HEALTHCARE', 'Healthcare'),
    ('EDUCATION','Education'),
    ('CONSTRUCTION', 'Construction'),
    ('MANUFACTURING','Manufacturing'),
    ('RETAIL','Retail'),
    ('AGRICULTURE','Agriculture'),
    ('TRANSPORT','Transport'),
    ('HOSPITALITY','Hospitality'),
    ('ENERGY','Energy'),
    ('TELECOMMUNICATION','Telecommunications'),
    ('MEDIA','Media'),
    ('LEGAL','Legal'),
    ('GOVERNMENT','Government'),
    ('OTHER','Other')
   
]

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

EXPERIENCE_LEVEL_CHOICES = [
    ('ENTRY', 'Entry Level'),
    ('MID', 'Mid Level'),
    ('SENIOR', 'Senior'),
]

APPLICATION_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('INTERVIEW', 'Interview'),
    ('HIRED', 'Hired'),
    ('REJECTED', 'Rejected'),
]

NEXT_STEP_CHOICES = [
    ('DIRECT_HIRE', 'Direct Hire'),
    ('INTERVIEW', 'Interview'),
]

NEXT_STEP_TYPE_CHOICES = [
    ('INTERVIEW', 'Interview'),
    ('DIRECT_HIRE', 'Direct Hire'),
]

NEXT_STEP_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('APPROVED', 'Approved'),
    ('DECLINED', 'Declined'),
]

class Job(models.Model):
    recruiter = models.ForeignKey('authentication.RecruiterProfile', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.JSONField(default=list)
    salary_min = models.IntegerField()
    salary_max = models.IntegerField()
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    location = models.CharField(max_length=100)
    is_remote = models.BooleanField(default=False)
    posted_at = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateField()
    experience_level = models.CharField(max_length=30, choices=EXPERIENCE_LEVEL_CHOICES)
    benefits = models.JSONField(default=list, blank=True)
    recruiting_size = models.PositiveIntegerField(default=1, help_text="Number of positions open for this job")
    next_step = models.CharField(max_length=20, choices=NEXT_STEP_CHOICES, default='INTERVIEW', help_text="Next step for applicants: Direct Hire or Interview")
    skills = models.JSONField(default=list, blank=True, help_text="List of skills required for the job")

class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    seeker = models.ForeignKey('authentication.JobSeekerProfile', on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=APPLICATION_STATUS_CHOICES,
        default='PENDING'
    )
    recruiter_notes = models.TextField(blank=True)
    # Next step workflow fields
    selected_for_next_step = models.BooleanField(default=False)
    next_step_type = models.CharField(max_length=20, choices=NEXT_STEP_TYPE_CHOICES, blank=True, null=True)
    next_step_status = models.CharField(max_length=20, choices=NEXT_STEP_STATUS_CHOICES, blank=True, null=True)
    applicant_approved = models.BooleanField(default=False)
    job_duration_days = models.PositiveIntegerField(blank=True, null=True, help_text="Job duration in days for direct hire")
    
    class Meta:
        # Ensure a job seeker can only apply once to a specific job
        unique_together = ('job', 'seeker')
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'

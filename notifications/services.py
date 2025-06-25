from .models import Notification
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

def create_notification(user, notification_type, title, message, related_object_id=None, related_object_type=None):
    """
    Create a notification for a specific user
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_object_id=related_object_id,
        related_object_type=related_object_type
    )
    return notification

def create_notification_for_recruiter(recruiter, notification_type, title, message, related_object_id=None, related_object_type=None):
    """
    Create a notification for a recruiter
    """
    return create_notification(
        recruiter.user, 
        notification_type, 
        title, 
        message, 
        related_object_id, 
        related_object_type
    )

def create_notification_for_seeker(seeker, notification_type, title, message, related_object_id=None, related_object_type=None):
    """
    Create a notification for a job seeker
    """
    return create_notification(
        seeker.user, 
        notification_type, 
        title, 
        message, 
        related_object_id, 
        related_object_type
    )

def create_application_notification(application):
    """
    Create notifications for both recruiter and seeker when a new application is created
    """
    # Notification for recruiter
    create_notification_for_recruiter(
        application.job.recruiter,
        'application',
        'New Application Received',
        f'A new application was received for {application.job.title}',
        application.id,
        'application'
    )
    
    # Notification for seeker
    create_notification_for_seeker(
        application.seeker,
        'application',
        'Application Submitted',
        f'Your application for {application.job.title} has been submitted successfully',
        application.id,
        'application'
    )

def create_application_status_notification(application):
    """
    Create notification for job seeker when application status changes
    """
    create_notification_for_seeker(
        application.seeker,
        'application_status',
        'Application Status Updated',
        f'Your application for {application.job.title} has been updated to {application.status}',
        application.id,
        'application'
    )

def create_job_match_notification(seeker, job):
    """
    Create notification for job seeker when a new job match is found
    """
    create_notification_for_seeker(
        seeker,
        'job_match',
        'New Job Match Found',
        f'We found a new job that matches your profile: {job.title} at {job.company_name}',
        job.id,
        'job'
    )

def create_candidate_match_notification(recruiter, job, seeker):
    """
    Create notification for recruiter when a new candidate match is found
    """
    create_notification_for_recruiter(
        recruiter,
        'candidate_match',
        'New Candidate Match Found',
        f'We found a new candidate that matches your job {job.title}: {seeker.full_name}',
        job.id,
        'job'
    )

def create_interview_notification(application, interview_date, interview_type):
    """
    Create notifications for both recruiter and seeker when an interview is scheduled
    """
    # Notification for recruiter
    create_notification_for_recruiter(
        application.job.recruiter,
        'interview',
        'Interview Scheduled',
        f'An interview has been scheduled for {application.seeker.full_name} on {interview_date}',
        application.id,
        'application'
    )
    
    # Notification for seeker
    create_notification_for_seeker(
        application.seeker,
        'interview',
        'Interview Scheduled',
        f'An interview has been scheduled for {application.job.title} on {interview_date}. Type: {interview_type}',
        application.id,
        'application'
    )

def create_feedback_notification(seeker, recruiter):
    """
    Create notification for job seeker when they receive feedback
    """
    create_notification_for_seeker(
        seeker,
        'feedback',
        'New Feedback Received',
        f'You have received new feedback from {recruiter.company_name}',
        seeker.id,
        'seeker'
    )

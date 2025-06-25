from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('application', 'New Application'),
        ('job_match', 'New Job Match'),
        ('candidate_match', 'New Candidate Match'),
        ('application_status', 'Application Status Update'),
        ('interview', 'Interview Scheduled'),
        ('feedback', 'New Feedback'),
        ('message', 'New Message'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    related_object_id = models.IntegerField(null=True, blank=True)  # ID of related object (job, application, etc.)
    related_object_type = models.CharField(max_length=50, blank=True)  # Type of related object
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type}: {self.title} for {self.user.email}"

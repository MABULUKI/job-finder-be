from rest_framework import serializers
from .models import Job, Application
from django.utils import timezone


class JobSerializer(serializers.ModelSerializer):
    applicant_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'requirements', 'salary_min', 'salary_max',
                 'job_type', 'location', 'is_remote', 'application_deadline',
                 'experience_level', 'benefits', 'recruiting_size', 'next_step', 'skills',
                 'applicant_count', 'is_active', 'posted_at']
        read_only_fields = ['recruiter', 'applicant_count', 'is_active']
        
    def get_applicant_count(self, obj):
        return Application.objects.filter(job=obj).count()
        
    def get_is_active(self, obj):
        # A job is considered active if its application deadline is in the future
        return obj.application_deadline >= timezone.now().date()

class ApplicationSerializer(serializers.ModelSerializer):
    seeker_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = ['id', 'job', 'seeker', 'status', 'applied_at', 'cover_letter', 'seeker_details']
        read_only_fields = ['seeker']
        
    def get_seeker_details(self, obj):
        seeker = obj.seeker
        # Try to get feedback data if available
        feedbacks = []
        try:
            from feedback.models import Feedback
            feedbacks_queryset = Feedback.objects.filter(recipient=seeker.user)
            feedbacks = [
                {
                    'rating': feedback.rating,
                    'comment': feedback.comment,
                    'created_at': feedback.created_at.strftime('%Y-%m-%d'),
                    'provider_name': feedback.provider.get_full_name() if feedback.provider else 'Anonymous'
                } for feedback in feedbacks_queryset
            ]
        except ImportError:
            # Feedback module might not be available
            pass
            
        return {
            'id': seeker.id,
            'full_name': seeker.full_name,
            'email': seeker.user.email,
            'phone': seeker.phone,
            'skills': seeker.skills,
            'education': seeker.education,
            'experience': seeker.experience,
            'resume_url': seeker.resume.url if seeker.resume else None,
            'profile_picture': seeker.profile_picture.url if seeker.profile_picture else None,
            'linkedin': seeker.linkedin,
            'location': seeker.location,
            'willing_to_relocate': seeker.willing_to_relocate,
            'salary_expectation': seeker.salary_expectation,
            'average_rating': seeker.average_rating or 0.0,  # Default to 0.0 if None
            'feedback_count': seeker.feedback_count or 0,
            'feedbacks': feedbacks,
        }

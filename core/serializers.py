from rest_framework import serializers
from .models import Job, Application, FeedbackRating
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
    feedbacks = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = ['id', 'job', 'seeker', 'status', 'applied_at', 'cover_letter', 'seeker_details', 
                 'selected_for_next_step', 'next_step_type', 'next_step_status', 'applicant_approved',
                 'recruiter_notes', 'feedbacks']
        read_only_fields = ['seeker', 'feedbacks']
        
    def get_feedbacks(self, obj):
        # Get all feedbacks for this application
        feedbacks_queryset = FeedbackRating.objects.filter(application=obj, feedback_type='APPLICATION')
        if not feedbacks_queryset.exists():
            return []
            
        return [
            {
                'id': feedback.id,
                'rating': float(feedback.rating),
                'comment': feedback.comment,
                'created_at': feedback.created_at.strftime('%Y-%m-%d'),
                'recruiter_name': feedback.recruiter.company_name,
                'feedback_type': feedback.feedback_type
            } for feedback in feedbacks_queryset
        ]
        
    def get_seeker_details(self, obj):
        seeker = obj.seeker
        # Use the property methods from JobSeekerProfile to get ratings
        average_rating = seeker.average_rating or 0.0
        feedback_count = seeker.feedback_count
            
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
            'average_rating': average_rating,
            'feedback_count': feedback_count,
        }


class FeedbackRatingSerializer(serializers.ModelSerializer):
    recruiter_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FeedbackRating
        fields = ['id', 'application', 'profile', 'rating', 'comment', 'created_at', 
                 'recruiter_name', 'feedback_type']
        read_only_fields = ['recruiter', 'created_at', 'recruiter_name']
    
    def get_recruiter_name(self, obj):
        return obj.recruiter.company_name if obj.recruiter else 'Unknown'
    
    def validate_rating(self, value):
        """Ensure rating doesn't exceed 5.0"""
        if value > 5.0:
            return 5.0
        return value
    
    def create(self, validated_data):
        # Get the recruiter from the request
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not hasattr(request.user, 'recruiter_profile'):
            raise serializers.ValidationError("Only recruiters can provide feedback.")
        
        # Add the recruiter to the validated data
        validated_data['recruiter'] = request.user.recruiter_profile
        
        # Set default feedback type if not provided
        if 'feedback_type' not in validated_data:
            # If application is provided, it's an application feedback
            if validated_data.get('application'):
                validated_data['feedback_type'] = 'APPLICATION'
            else:
                validated_data['feedback_type'] = 'PROFILE'
        
        return super().create(validated_data)

from rest_framework import serializers
from .models import Job, Application, Feedback
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
        feedbacks_queryset = Feedback.objects.filter(application=obj)
        if not feedbacks_queryset.exists():
            return []
            
        return [
            {
                'id': feedback.id,
                'rating': float(feedback.rating),
                'comment': feedback.comment,
                'created_at': feedback.created_at.strftime('%Y-%m-%d'),
                'recruiter_name': feedback.recruiter.company_name
            } for feedback in feedbacks_queryset
        ]
        
    def get_seeker_details(self, obj):
        seeker = obj.seeker
        # Get all feedbacks for this seeker
        feedbacks_queryset = Feedback.objects.filter(profile=seeker)
        
        # Calculate average rating
        average_rating = 0.0
        if feedbacks_queryset.exists():
            total_rating = sum(float(feedback.rating) for feedback in feedbacks_queryset)
            average_rating = total_rating / feedbacks_queryset.count()
            
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
            'average_rating': round(average_rating, 1),
            'feedback_count': feedbacks_queryset.count(),
        }


class FeedbackSerializer(serializers.ModelSerializer):
    recruiter_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Feedback
        fields = ['id', 'application', 'profile', 'rating', 'comment', 'created_at', 'recruiter_name']
        read_only_fields = ['recruiter', 'created_at', 'recruiter_name']
    
    def get_recruiter_name(self, obj):
        return obj.recruiter.company_name if obj.recruiter else 'Unknown'
    
    def create(self, validated_data):
        # Get the recruiter from the request
        request = self.context.get('request')
        if not request or not hasattr(request, 'user') or not hasattr(request.user, 'recruiter_profile'):
            raise serializers.ValidationError("Only recruiters can provide feedback.")
        
        # Add the recruiter to the validated data
        validated_data['recruiter'] = request.user.recruiter_profile
        
        return super().create(validated_data)

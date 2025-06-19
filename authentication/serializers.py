from rest_framework import serializers
from .models import RecruiterProfile, JobSeekerProfile, SeekerFeedback

class RecruiterProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = RecruiterProfile
        fields = [
            'id', 'company_name', 'email', 'company_description', 'industry', 'company_size',
            'website', 'phone', 'address', 'logo'
        ]
        read_only_fields = ['id', 'email', 'company_name']

class SeekerFeedbackSerializer(serializers.ModelSerializer):
    recruiter = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = SeekerFeedback
        fields = ['id', 'seeker', 'recruiter', 'rating', 'comment', 'created_at']
        read_only_fields = ['recruiter', 'created_at']

class JobSeekerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    feedback_count = serializers.IntegerField(read_only=True)
    feedbacks = SeekerFeedbackSerializer(many=True, read_only=True)
    class Meta:
        model = JobSeekerProfile
        fields = [
            'id', 'user', 'full_name', 'email', 'skills', 'education', 'experience', 'resume',
            'preferred_job_types', 'salary_expectation', 'location', 'willing_to_relocate', 'is_available',
            'average_rating', 'feedback_count', 'feedbacks'
        ]
        read_only_fields = ['id', 'email', 'full_name', 'average_rating', 'feedback_count', 'feedbacks']

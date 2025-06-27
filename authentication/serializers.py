from rest_framework import serializers
from .models import RecruiterProfile, JobSeekerProfile
from core.models import FeedbackRating

class RecruiterProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = RecruiterProfile
        fields = [
            'id', 'company_name', 'email', 'company_description', 'industry', 'company_size',
            'website', 'phone', 'address', 'logo', 'profile_updated'
        ]
        read_only_fields = ['id', 'email', 'company_name']

class FeedbackRatingSerializer(serializers.ModelSerializer):
    recruiter = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = FeedbackRating
        fields = ['id', 'profile', 'recruiter', 'rating', 'comment', 'created_at', 'feedback_type', 'application']
        read_only_fields = ['recruiter', 'created_at']

class JobSeekerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    feedback_count = serializers.IntegerField(read_only=True)
    feedbacks = FeedbackRatingSerializer(source='all_feedbacks', many=True, read_only=True)
    class Meta:
        model = JobSeekerProfile
        fields = [
            'id', 'user', 'full_name', 'email', 'phone', 'linkedin', 'profile_picture', 'skills', 'education', 'experience', 'resume',
            'preferred_job_types', 'salary_expectation', 'location', 'willing_to_relocate', 'is_available', 'profile_updated',
            'average_rating', 'feedback_count', 'feedbacks'
        ]
        read_only_fields = ['id', 'user', 'email', 'average_rating', 'feedback_count', 'feedbacks']

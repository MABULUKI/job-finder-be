from rest_framework import serializers
from .models import Job, Application



class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'requirements', 'salary_min', 'salary_max',
                 'job_type', 'location', 'is_remote', 'application_deadline',
                 'experience_level', 'benefits', 'recruiting_size', 'next_step', 'skills']
        read_only_fields = ['recruiter']

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['seeker']

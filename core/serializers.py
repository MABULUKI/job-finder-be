from rest_framework import serializers
from .models import Job, Application



class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'next_step', 'company', 'location', 'job_type', 'category', 'created_at', 'updated_at']

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['seeker']

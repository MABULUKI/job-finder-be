from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'related_object_id', 
                  'related_object_type', 'created_at', 'created_at_formatted', 'is_read']
    
    def get_created_at_formatted(self, obj):
        return obj.created_at.strftime("%b %d, %Y, %H:%M")

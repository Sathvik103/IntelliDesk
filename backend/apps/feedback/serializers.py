from rest_framework import serializers
from .models import Feedback
from apps.accounts.serializers import UserSerializer

class FeedbackSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    request_description = serializers.CharField(source='request.custom_description', read_only=True)

    class Meta:
        model = Feedback
        fields = [
            'id',
            'request',
            'request_description',
            'user',
            'user_name',
            'employee',
            'employee_name',
            'is_resolved',
            'rating',
            'comments',
            'resolution_time_minutes',
            'met_sla',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'employee', 'resolution_time_minutes', 'met_sla', 'created_at']

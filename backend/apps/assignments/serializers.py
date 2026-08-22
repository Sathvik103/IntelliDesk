from rest_framework import serializers
from .models import Assignment
from apps.employees.serializers import EmployeeSerializer

class AssignmentSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    request_domain_name = serializers.CharField(source='request.domain.name', read_only=True)
    request_priority = serializers.CharField(source='request.priority', read_only=True)
    request_description = serializers.CharField(source='request.custom_description', read_only=True)
    request_location_name = serializers.CharField(source='request.location_name', read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id',
            'request',
            'request_domain_name',
            'request_priority',
            'request_description',
            'request_location_name',
            'employee',
            'employee_details',
            'status',
            'status_display',
            'request_latitude_snapshot',
            'request_longitude_snapshot',
            'employee_latitude_snapshot',
            'employee_longitude_snapshot',
            'distance_km',
            'active_workload_at_assignment',
            'features_snapshot',
            'suitability_score',
            'ranking_model_version',
            'notes',
            'assigned_at',
            'accepted_at',
            'completed_at',
            'reassigned_at',
        ]
        read_only_fields = ['id', 'assigned_at', 'accepted_at', 'completed_at', 'reassigned_at']

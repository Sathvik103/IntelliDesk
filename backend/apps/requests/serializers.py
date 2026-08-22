from rest_framework import serializers
from .models import ServiceRequest
from apps.services.serializers import ServiceDomainSerializer, PredefinedIssueSerializer
from apps.accounts.serializers import UserSerializer

class ServiceRequestSerializer(serializers.ModelSerializer):
    domain_details = ServiceDomainSerializer(source='domain', read_only=True)
    predefined_issue_details = PredefinedIssueSerializer(source='predefined_issue', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    active_assignment = serializers.SerializerMethodField()
    feedback_details = serializers.SerializerMethodField()

    class Meta:
        model = ServiceRequest
        fields = [
            'id',
            'organization',
            'user',
            'user_details',
            'domain',
            'domain_details',
            'predefined_issue',
            'predefined_issue_details',
            'custom_description',
            'latitude',
            'longitude',
            'location_name',
            'priority',
            'priority_display',
            'status',
            'status_display',
            'active_assignment',
            'feedback_details',
            'created_at',
            'in_progress_at',
            'completed_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'organization', 'status', 'created_at', 'in_progress_at', 'completed_at', 'updated_at']

    def get_active_assignment(self, obj):
        assignment = obj.assignments.filter(
            status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED']
        ).first()
        if not assignment:
            return None
        return {
            'id': str(assignment.id),
            'employee_id': str(assignment.employee_id),
            'employee_name': assignment.employee.user.get_full_name() or assignment.employee.user.username,
            'employee_phone': assignment.employee.user.phone,
            'role_title': assignment.employee.role.title if assignment.employee.role else 'Technician',
            'status': assignment.status,
            'distance_km': float(assignment.distance_km),
            'suitability_score': assignment.suitability_score,
            'ranking_model_version': assignment.ranking_model_version,
            'assigned_at': assignment.assigned_at,
            'completed_at': assignment.completed_at,
        }

    def get_feedback_details(self, obj):
        if hasattr(obj, 'feedback'):
            fb = obj.feedback
            return {
                'id': str(fb.id),
                'rating': fb.rating,
                'is_resolved': fb.is_resolved,
                'comments': fb.comments,
                'resolution_time_minutes': fb.resolution_time_minutes,
                'met_sla': fb.met_sla,
                'created_at': fb.created_at,
            }
        return None

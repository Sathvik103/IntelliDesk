from rest_framework import serializers
from .models import ServiceDomain, PredefinedIssue

class PredefinedIssueSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source='domain.name', read_only=True)
    default_priority_display = serializers.CharField(source='get_default_priority_display', read_only=True)

    class Meta:
        model = PredefinedIssue
        fields = [
            'id',
            'domain',
            'domain_name',
            'title',
            'default_priority',
            'default_priority_display',
            'estimated_duration_minutes',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

class ServiceDomainSerializer(serializers.ModelSerializer):
    predefined_issues = PredefinedIssueSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceDomain
        fields = [
            'id',
            'organization',
            'organization_name',
            'name',
            'description',
            'sla_hours',
            'icon_name',
            'is_active',
            'predefined_issues',
            'employee_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

    def get_employee_count(self, obj):
        return obj.employee_skills.filter(employee__status='ACTIVE').count()

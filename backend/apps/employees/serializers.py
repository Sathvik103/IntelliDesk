from rest_framework import serializers
from .models import Employee, EmployeeRole, EmployeeSkill, EmployeeSchedule
from apps.accounts.serializers import UserSerializer
from apps.services.serializers import ServiceDomainSerializer

class EmployeeRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeRole
        fields = ['id', 'organization', 'title', 'description']
        read_only_fields = ['id', 'organization']

class EmployeeSkillSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source='domain.name', read_only=True)

    class Meta:
        model = EmployeeSkill
        fields = [
            'id',
            'employee',
            'domain',
            'domain_name',
            'proficiency_level',
            'years_of_experience',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

class EmployeeScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = EmployeeSchedule
        fields = [
            'id',
            'employee',
            'day_of_week',
            'day_name',
            'start_time',
            'end_time',
            'is_active',
        ]
        read_only_fields = ['id']

class EmployeeSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    role_details = EmployeeRoleSerializer(source='role', read_only=True)
    skills = EmployeeSkillSerializer(many=True, read_only=True)
    schedules = EmployeeScheduleSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    active_assignments_count = serializers.SerializerMethodField()
    historical_avg_rating = serializers.SerializerMethodField()
    historical_completed_count = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'user',
            'user_details',
            'organization',
            'role',
            'role_details',
            'experience_years',
            'max_active_assignments',
            'current_latitude',
            'current_longitude',
            'status',
            'status_display',
            'is_available',
            'skills',
            'schedules',
            'active_assignments_count',
            'historical_avg_rating',
            'historical_completed_count',
            'last_location_updated_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_location_updated_at']

    def get_active_assignments_count(self, obj):
        return obj.assignments.filter(status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']).count()

    def get_historical_avg_rating(self, obj):
        feedbacks = obj.assignments.filter(status='COMPLETED', request__feedback__isnull=False)
        ratings = [f.request.feedback.rating for f in feedbacks if hasattr(f.request, 'feedback')]
        if ratings:
            return round(sum(ratings) / len(ratings), 2)
        return 5.0 # Default starting rating for new staff

    def get_historical_completed_count(self, obj):
        return obj.assignments.filter(status='COMPLETED').count()

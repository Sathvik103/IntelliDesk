from datetime import datetime
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Employee, EmployeeRole, EmployeeSkill, EmployeeSchedule
from .serializers import (
    EmployeeSerializer,
    EmployeeRoleSerializer,
    EmployeeSkillSerializer,
    EmployeeScheduleSerializer,
)
from apps.accounts.permissions import IsAdminRole, IsEmployeeRole


class EmployeeRoleViewSet(viewsets.ModelViewSet):
    """
    Employee role management (e.g. 'Senior Electrician', 'Plumber').
    Roles are distinct from service domains/skills.
    Read: any authenticated user in org. Write: admin only.
    """
    serializer_class = EmployeeRoleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return EmployeeRole.objects.none()
        if user.is_superuser:
            return EmployeeRole.objects.all().select_related('organization')
        return EmployeeRole.objects.filter(
            organization=user.organization
        ).select_related('organization')

    def perform_create(self, serializer):
        if not self.request.user.is_superuser and self.request.user.organization:
            serializer.save(organization=self.request.user.organization)
        else:
            serializer.save()


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Employee CRUD and management.
    Read/availability toggle: authenticated users.
    Create/Update/Delete/Status: admin only.
    """
    serializer_class = EmployeeSerializer
    filterset_fields = ['status', 'is_available', 'role']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'role__title']
    ordering_fields = ['created_at', 'experience_years', 'user__first_name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'me', 'update_location', 'toggle_availability', 'is_on_schedule']:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Employee.objects.none()
        qs = Employee.objects.select_related(
            'user', 'role', 'organization'
        ).prefetch_related('skills__domain', 'schedules')
        if user.is_superuser:
            return qs
        return qs.filter(organization=user.organization)

    @action(detail=False, methods=['get'], permission_classes=[IsEmployeeRole])
    def me(self, request):
        """Return the authenticated employee's own profile."""
        try:
            emp = Employee.objects.select_related(
                'user', 'role', 'organization'
            ).prefetch_related('skills__domain', 'schedules').get(user=request.user)
            return Response(self.get_serializer(emp).data)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'No employee profile linked to current user.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['patch'])
    def update_location(self, request, pk=None):
        """Update an employee's current operational location."""
        emp = self.get_object()
        if request.user.role != 'ADMIN' and emp.user != request.user:
            return Response(
                {'error': 'Unauthorized to update this employee location.'},
                status=status.HTTP_403_FORBIDDEN
            )
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        if lat is None or lng is None:
            return Response(
                {'error': 'Both latitude and longitude are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        emp.current_latitude = lat
        emp.current_longitude = lng
        emp.save(update_fields=['current_latitude', 'current_longitude', 'last_location_updated_at'])
        return Response({'status': 'location updated', 'latitude': lat, 'longitude': lng})

    @action(detail=True, methods=['patch'])
    def toggle_availability(self, request, pk=None):
        """Toggle or explicitly set an employee's is_available flag."""
        emp = self.get_object()
        if request.user.role != 'ADMIN' and emp.user != request.user:
            return Response(
                {'error': 'Unauthorized to toggle availability.'},
                status=status.HTTP_403_FORBIDDEN
            )
        is_available = request.data.get('is_available')
        emp.is_available = bool(is_available) if is_available is not None else not emp.is_available
        emp.save(update_fields=['is_available'])
        return Response({'status': 'availability updated', 'is_available': emp.is_available})

    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        """
        Set an employee's operational status.
        Valid values: ACTIVE, ON_LEAVE, OFF_DUTY, INACTIVE
        """
        emp = self.get_object()
        new_status = request.data.get('status', '').upper()
        valid = [s[0] for s in Employee.Status.choices]
        if new_status not in valid:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        emp.status = new_status
        # When setting to INACTIVE or OFF_DUTY, clear availability
        if new_status in ['INACTIVE', 'OFF_DUTY']:
            emp.is_available = False
            emp.save(update_fields=['status', 'is_available'])
        else:
            emp.save(update_fields=['status'])
        return Response({'status': 'updated', 'new_status': new_status})

    @action(detail=True, methods=['get'])
    def is_on_schedule(self, request, pk=None):
        """
        Check whether the employee is currently within a configured working schedule.
        Returns: { on_schedule: bool, current_day: str, current_time: str, schedule_entry: {...} | null }
        """
        emp = self.get_object()
        now = timezone.localtime(timezone.now())
        current_day = now.weekday()   # 0=Monday … 6=Sunday
        current_time = now.time()

        schedule_entry = emp.schedules.filter(
            day_of_week=current_day,
            is_active=True,
            start_time__lte=current_time,
            end_time__gte=current_time,
        ).first()

        return Response({
            'on_schedule': schedule_entry is not None,
            'current_day': now.strftime('%A'),
            'current_time': current_time.strftime('%H:%M'),
            'schedule_entry': EmployeeScheduleSerializer(schedule_entry).data if schedule_entry else None,
        })


class EmployeeSkillViewSet(viewsets.ModelViewSet):
    """
    Employee skill (domain + proficiency) management.
    Read: authenticated. Write: admin only.
    Employees can only have one skill record per domain (enforced by model constraint).
    """
    serializer_class = EmployeeSkillSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return EmployeeSkill.objects.none()
        if user.is_superuser:
            return EmployeeSkill.objects.all().select_related('employee__user', 'domain')
        return EmployeeSkill.objects.filter(
            employee__organization=user.organization
        ).select_related('employee__user', 'domain')

    def perform_create(self, serializer):
        """Validate the target employee belongs to the requesting admin's organization."""
        if not self.request.user.is_superuser:
            employee = serializer.validated_data.get('employee')
            if employee and employee.organization != self.request.user.organization:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You can only manage skills for employees in your organization.')
        serializer.save()


class EmployeeScheduleViewSet(viewsets.ModelViewSet):
    """
    Employee working schedule management.
    Read: authenticated. Write: admin only.
    """
    serializer_class = EmployeeScheduleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return EmployeeSchedule.objects.none()
        if user.is_superuser:
            return EmployeeSchedule.objects.all().select_related('employee__user')
        return EmployeeSchedule.objects.filter(
            employee__organization=user.organization
        ).select_related('employee__user')

    def perform_create(self, serializer):
        """Validate the target employee belongs to the requesting admin's organization."""
        if not self.request.user.is_superuser:
            employee = serializer.validated_data.get('employee')
            if employee and employee.organization != self.request.user.organization:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('You can only manage schedules for employees in your organization.')
        serializer.save()


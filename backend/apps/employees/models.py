import uuid
from django.db import models
from django.conf import settings
from apps.organizations.models import Organization
from apps.services.models import ServiceDomain

class EmployeeRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='employee_roles'
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'employee_roles'
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(fields=['organization', 'title'], name='unique_role_per_org')
        ]

    def __str__(self):
        return f"{self.title} ({self.organization.name})"

class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active / On Duty'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'
        OFF_DUTY = 'OFF_DUTY', 'Off Duty'
        INACTIVE = 'INACTIVE', 'Inactive / Terminated'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='employees'
    )
    role = models.ForeignKey(
        EmployeeRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    experience_years = models.PositiveIntegerField(default=1)
    max_active_assignments = models.PositiveIntegerField(
        default=3,
        help_text="Maximum concurrent active requests this employee can handle"
    )
    current_latitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    current_longitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_available = models.BooleanField(
        default=True,
        help_text="Quick toggle for immediate ad-hoc availability"
    )
    last_location_updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status', 'is_available']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.role.title if self.role else 'Technician'})"

class EmployeeSkill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    domain = models.ForeignKey(
        ServiceDomain,
        on_delete=models.CASCADE,
        related_name='employee_skills'
    )
    proficiency_level = models.PositiveSmallIntegerField(
        default=3,
        help_text="Proficiency from 1 (Novice) to 5 (Master/Expert)"
    )
    years_of_experience = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employee_skills'
        constraints = [
            models.UniqueConstraint(fields=['employee', 'domain'], name='unique_skill_per_employee')
        ]
        indexes = [
            models.Index(fields=['domain', 'proficiency_level']),
        ]

    def __str__(self):
        return f"{self.employee} - {self.domain.name} (Lvl {self.proficiency_level})"

class EmployeeSchedule(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'Monday'
        TUESDAY = 1, 'Tuesday'
        WEDNESDAY = 2, 'Wednesday'
        THURSDAY = 3, 'Thursday'
        FRIDAY = 4, 'Friday'
        SATURDAY = 5, 'Saturday'
        SUNDAY = 6, 'Sunday'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField(default='09:00:00')
    end_time = models.TimeField(default='18:00:00')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'employee_schedules'
        ordering = ['day_of_week', 'start_time']
        constraints = [
            models.UniqueConstraint(fields=['employee', 'day_of_week'], name='unique_schedule_day_per_employee')
        ]

    def __str__(self):
        return f"{self.employee} - {self.get_day_of_week_display()}: {self.start_time} to {self.end_time}"

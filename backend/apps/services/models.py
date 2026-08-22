import uuid
from django.db import models
from apps.organizations.models import Organization

class ServiceDomain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='service_domains'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    sla_hours = models.PositiveIntegerField(default=24, help_text="Default SLA resolution target in hours")
    icon_name = models.CharField(max_length=50, blank=True, default='Wrench')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_domains'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['organization', 'name'], name='unique_domain_per_org')
        ]
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

class PredefinedIssue(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
        CRITICAL = 'CRITICAL', 'Critical'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(
        ServiceDomain,
        on_delete=models.CASCADE,
        related_name='predefined_issues'
    )
    title = models.CharField(max_length=255)
    default_priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    estimated_duration_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'predefined_issues'
        ordering = ['title']
        indexes = [
            models.Index(fields=['domain', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} [{self.domain.name}]"

import uuid
from django.db import models
from django.conf import settings
from apps.organizations.models import Organization
from apps.services.models import ServiceDomain, PredefinedIssue

class ServiceRequest(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        NORMAL = 'NORMAL', 'Normal'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        QUEUED = 'QUEUED', 'Queued for Assignment'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        REOPENED = 'REOPENED', 'Reopened'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='service_requests'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='raised_requests'
    )
    domain = models.ForeignKey(
        ServiceDomain,
        on_delete=models.CASCADE,
        related_name='service_requests'
    )
    predefined_issue = models.ForeignKey(
        PredefinedIssue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_requests'
    )
    custom_description = models.TextField(blank=True, default='')
    details_snapshot = models.JSONField(default=dict, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    location_name = models.CharField(max_length=255, blank=True, default='')
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    in_progress_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['domain', 'status']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        title = self.predefined_issue.title if self.predefined_issue else (self.custom_description[:40] or "Service Request")
        return f"[{self.priority}] {title} ({self.status})"

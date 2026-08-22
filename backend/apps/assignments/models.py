import uuid
from django.db import models
from apps.requests.models import ServiceRequest
from apps.employees.models import Employee
from apps.services.models import ServiceDomain


class Assignment(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = 'ASSIGNED', 'Assigned'
        ACCEPTED = 'ACCEPTED', 'Accepted by Staff'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        REASSIGNED = 'REASSIGNED', 'Reassigned'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED
    )

    # ─── Assignment-Time Context Snapshots ───────────────────────────────────
    # These columns record point-in-time facts that must be preserved exactly
    # as they existed when the assignment decision was made.
    # They are stored as explicit relational columns (not only in JSON) so that
    # analytics queries and future ML training datasets can use standard SQL.

    # Domain/Priority captured at assignment time
    domain_snapshot = models.ForeignKey(
        ServiceDomain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignment_snapshots',
        help_text="Service domain at assignment time"
    )
    priority_snapshot = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Request priority at assignment time (LOW/NORMAL/HIGH/URGENT/CRITICAL)"
    )

    # Geographic snapshot
    request_latitude_snapshot = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    request_longitude_snapshot = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    employee_latitude_snapshot = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    employee_longitude_snapshot = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=0.0,
        help_text="Haversine distance from employee to request location at assignment time (km)"
    )

    # Employee state snapshots at assignment time
    active_workload_at_assignment = models.PositiveIntegerField(
        default=0,
        help_text="Number of active assignments the employee had at assignment time"
    )
    skill_proficiency_snapshot = models.PositiveSmallIntegerField(
        default=0,
        help_text="Employee's domain proficiency level (1–5) at assignment time"
    )
    experience_years_snapshot = models.PositiveIntegerField(
        default=0,
        help_text="Employee's total experience_years at assignment time"
    )
    is_available_snapshot = models.BooleanField(
        default=True,
        help_text="Employee's is_available flag at assignment time"
    )

    # SLA tracking
    sla_hours_snapshot = models.PositiveIntegerField(
        default=0,
        help_text="Domain SLA target in hours at assignment time"
    )
    met_sla = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether the assignment was resolved within SLA (null = not yet determined)"
    )

    # Ranking engine metadata
    suitability_score = models.FloatField(
        default=0.0,
        help_text="Suitability score returned by the ranking engine [0.0 – 1.0]"
    )
    ranking_model_version = models.CharField(
        max_length=100,
        default='placeholder-deterministic-v1',
        help_text="Identifier of the ranking engine or ML model that produced this score"
    )

    # Reassignment tracking
    is_reassignment = models.BooleanField(
        default=False,
        help_text="True if this assignment replaced a previous one for the same request"
    )
    reassignment_reason = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Reason provided when a request was reassigned"
    )

    # Complete feature vector (JSON backup alongside explicit columns)
    features_snapshot = models.JSONField(
        default=dict,
        help_text=(
            "Complete structured feature vector preserved at assignment time. "
            "Supplements the explicit columns above for full ML training reproducibility."
        )
    )

    notes = models.TextField(blank=True, default='')

    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'assignments'
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['request', 'status']),
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['assigned_at']),
            models.Index(fields=['domain_snapshot', 'status']),
            models.Index(fields=['priority_snapshot']),
            models.Index(fields=['met_sla']),
        ]

    def __str__(self):
        return f"Assignment #{str(self.id)[:8]}: Req {str(self.request_id)[:8]} -> {self.employee} ({self.status})"


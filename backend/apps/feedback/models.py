import uuid
from django.db import models
from django.conf import settings
from apps.requests.models import ServiceRequest
from apps.employees.models import Employee

class Feedback(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_feedbacks'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='received_feedbacks'
    )
    is_resolved = models.BooleanField(
        default=True,
        help_text="Whether the resident confirms the problem was fully solved"
    )
    rating = models.PositiveSmallIntegerField(
        default=5,
        help_text="User rating on a 1 to 5 scale"
    )
    comments = models.TextField(blank=True, default='')
    resolution_time_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Total elapsed time from request creation to completion in minutes"
    )
    met_sla = models.BooleanField(
        default=True,
        help_text="Whether the resolution occurred within the domain SLA timeframe"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'rating']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['met_sla']),
        ]

    def __str__(self):
        return f"Feedback for Req {str(self.request_id)[:8]}: {self.rating}/5 Stars (Resolved: {self.is_resolved})"

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.organizations.models import Organization

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        EMPLOYEE = 'EMPLOYEE', 'Employee / Workforce'
        USER = 'USER', 'Resident / Customer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER
    )
    phone = models.CharField(max_length=30, blank=True, default='')
    address = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        org_name = self.organization.name if self.organization else "Global"
        return f"{self.username} [{self.get_role_display()}] ({org_name})"

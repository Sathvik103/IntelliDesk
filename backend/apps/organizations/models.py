import uuid
from django.db import models

class Organization(models.Model):
    class OrgType(models.TextChoices):
        RESIDENTIAL_COLONY = 'RESIDENTIAL_COLONY', 'Residential Colony'
        GATED_COMMUNITY = 'GATED_COMMUNITY', 'Gated Community'
        OFFICE_SPACE = 'OFFICE_SPACE', 'Office Space'
        COMMERCIAL_COMPLEX = 'COMMERCIAL_COMPLEX', 'Commercial Complex'
        EDUCATIONAL_CAMPUS = 'EDUCATIONAL_CAMPUS', 'Educational Campus'
        OTHER = 'OTHER', 'Other Organization Type'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    org_type = models.CharField(max_length=50, choices=OrgType.choices, default=OrgType.RESIDENTIAL_COLONY)
    address = models.TextField(blank=True, default='')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, default=0.0)
    contact_email = models.EmailField(blank=True, default='')
    contact_phone = models.CharField(max_length=30, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['org_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_org_type_display()})"

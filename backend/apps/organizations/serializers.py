from rest_framework import serializers
from .models import Organization

class OrganizationSerializer(serializers.ModelSerializer):
    org_type_display = serializers.CharField(source='get_org_type_display', read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'org_type',
            'org_type_display',
            'address',
            'latitude',
            'longitude',
            'contact_email',
            'contact_phone',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

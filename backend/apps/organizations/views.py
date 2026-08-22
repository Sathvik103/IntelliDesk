from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Organization
from .serializers import OrganizationSerializer
from apps.accounts.permissions import IsAdminRole


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    Organization management API.
    - List/Retrieve: any authenticated user (scoped to their own org unless superuser)
    - Create/Update/Delete: admin role or superuser only
    """
    serializer_class = OrganizationSerializer
    filterset_fields = ['org_type', 'is_active']
    search_fields = ['name', 'address', 'contact_email']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'org_types']:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Organization.objects.none()
        if user.is_superuser:
            return Organization.objects.all()
        # Non-superusers see only their own organization
        if user.organization_id:
            return Organization.objects.filter(id=user.organization_id)
        return Organization.objects.none()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Set organization is_active = True."""
        org = self.get_object()
        org.is_active = True
        org.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'activated', 'id': str(org.id), 'name': org.name})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Set organization is_active = False."""
        org = self.get_object()
        org.is_active = False
        org.save(update_fields=['is_active', 'updated_at'])
        return Response({'status': 'deactivated', 'id': str(org.id), 'name': org.name})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def org_types(self, request):
        """Return all available organization type choices."""
        return Response([
            {'value': value, 'label': label}
            for value, label in Organization.OrgType.choices
        ])


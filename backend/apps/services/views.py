from rest_framework import viewsets, permissions
from .models import ServiceDomain, PredefinedIssue
from .serializers import ServiceDomainSerializer, PredefinedIssueSerializer
from apps.accounts.permissions import IsAdminRole

class ServiceDomainViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceDomainSerializer
    filterset_fields = ['organization', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sla_hours', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ServiceDomain.objects.none()
        if user.is_superuser:
            return ServiceDomain.objects.all().prefetch_related('predefined_issues')
        return ServiceDomain.objects.filter(
            organization=user.organization
        ).prefetch_related('predefined_issues')

    def perform_create(self, serializer):
        if not self.request.user.is_superuser and self.request.user.organization:
            serializer.save(organization=self.request.user.organization)
        else:
            serializer.save()

class PredefinedIssueViewSet(viewsets.ModelViewSet):
    serializer_class = PredefinedIssueSerializer
    filterset_fields = ['domain', 'default_priority', 'is_active']
    search_fields = ['title']
    ordering_fields = ['title', 'estimated_duration_minutes']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [IsAdminRole()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return PredefinedIssue.objects.none()
        if user.is_superuser:
            return PredefinedIssue.objects.all().select_related('domain')
        return PredefinedIssue.objects.filter(
            domain__organization=user.organization
        ).select_related('domain')

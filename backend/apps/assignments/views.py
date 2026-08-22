from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Assignment
from .serializers import AssignmentSerializer
from apps.ml_engine.service import AssignmentService

class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    filterset_fields = ['status', 'employee', 'request']
    ordering_fields = ['assigned_at', 'distance_km', 'suitability_score']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Assignment.objects.none()

        if user.is_superuser:
            return Assignment.objects.all().select_related(
                'request__domain', 'request__user', 'employee__user', 'employee__role'
            )

        if user.role == 'ADMIN':
            return Assignment.objects.filter(
                request__organization=user.organization
            ).select_related(
                'request__domain', 'request__user', 'employee__user', 'employee__role'
            )

        if user.role == 'EMPLOYEE':
            return Assignment.objects.filter(
                employee__user=user
            ).select_related(
                'request__domain', 'request__user', 'employee__user', 'employee__role'
            )

        # Resident sees assignments for their own requests
        return Assignment.objects.filter(
            request__user=user
        ).select_related(
            'request__domain', 'request__user', 'employee__user', 'employee__role'
        )

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        assignment = self.get_object()
        assignment.status = Assignment.Status.ACCEPTED
        assignment.accepted_at = timezone.now()
        assignment.save(update_fields=['status', 'accepted_at'])
        return Response({'status': 'ACCEPTED', 'accepted_at': assignment.accepted_at})

    @action(detail=True, methods=['post'])
    def reassign(self, request, pk=None):
        assignment = self.get_object()
        reason = request.data.get('reason', 'Manual or system trigger reassignment')
        assignment_service = AssignmentService()
        new_assignment, msg = assignment_service.reassign_request(assignment.request, reason=reason)
        return Response({
            'message': msg,
            'new_assignment_id': str(new_assignment.id) if new_assignment else None
        })

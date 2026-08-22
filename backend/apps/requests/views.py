from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import ServiceRequest
from .serializers import ServiceRequestSerializer
from apps.ml_engine.service import AssignmentService
from apps.assignments.models import Assignment

class ServiceRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceRequestSerializer
    filterset_fields = ['domain', 'priority', 'status', 'organization']
    search_fields = ['custom_description', 'location_name', 'user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'priority', 'status']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ServiceRequest.objects.none()

        if user.is_superuser:
            return ServiceRequest.objects.all().select_related(
                'organization', 'user', 'domain', 'predefined_issue'
            ).prefetch_related('assignments__employee__user', 'assignments__employee__role')

        if user.role == 'ADMIN':
            return ServiceRequest.objects.filter(
                organization=user.organization
            ).select_related(
                'organization', 'user', 'domain', 'predefined_issue'
            ).prefetch_related('assignments__employee__user', 'assignments__employee__role')

        if user.role == 'EMPLOYEE':
            # Employee sees requests assigned to them or within organization if relevant
            return ServiceRequest.objects.filter(
                organization=user.organization,
                assignments__employee__user=user
            ).distinct().select_related(
                'organization', 'user', 'domain', 'predefined_issue'
            ).prefetch_related('assignments__employee__user', 'assignments__employee__role')

        # Resident / Customer: sees only their own requests
        return ServiceRequest.objects.filter(
            user=user
        ).select_related(
            'organization', 'user', 'domain', 'predefined_issue'
        ).prefetch_related('assignments__employee__user', 'assignments__employee__role')

    def perform_create(self, serializer):
        user = self.request.user
        org = user.organization
        # If user did not provide custom coordinates, fallback to organization coordinates or user location
        lat = self.request.data.get('latitude') or (org.latitude if org else 0.0)
        lng = self.request.data.get('longitude') or (org.longitude if org else 0.0)
        
        request_obj = serializer.save(
            user=user,
            organization=org,
            latitude=lat,
            longitude=lng
        )

        # Execute automated workforce assignment
        assignment_service = AssignmentService()
        assignment, msg = assignment_service.auto_assign(request_obj)
        return request_obj

    @action(detail=True, methods=['post'])
    def trigger_assignment(self, request, pk=None):
        """Allows manually triggering or re-running the automated assignment engine"""
        service_request = self.get_object()
        assignment_service = AssignmentService()
        assignment, msg = assignment_service.auto_assign(service_request)
        return Response({
            'message': msg,
            'assignment_id': str(assignment.id) if assignment else None,
            'status': service_request.status
        })

    @action(detail=True, methods=['get'])
    def candidates_preview(self, request, pk=None):
        """Admin inspector for candidate eligibility, features, and ranking scores"""
        service_request = self.get_object()
        assignment_service = AssignmentService()
        candidates = assignment_service.inspect_candidates(service_request)
        return Response({
            'request_id': str(service_request.id),
            'domain': service_request.domain.name,
            'candidate_count': len(candidates),
            'candidates': candidates
        })

    @action(detail=True, methods=['post'])
    def start_work(self, request, pk=None):
        """Transitions request and assignment to IN_PROGRESS"""
        service_request = self.get_object()
        now = timezone.now()
        service_request.status = ServiceRequest.Status.IN_PROGRESS
        service_request.in_progress_at = now
        service_request.save(update_fields=['status', 'in_progress_at', 'updated_at'])

        # Update active assignment
        active_assignment = service_request.assignments.filter(
            status__in=[Assignment.Status.ASSIGNED, Assignment.Status.ACCEPTED]
        ).first()
        if active_assignment:
            active_assignment.status = Assignment.Status.IN_PROGRESS
            if not active_assignment.accepted_at:
                active_assignment.accepted_at = now
            active_assignment.save(update_fields=['status', 'accepted_at'])

        return Response({'status': 'IN_PROGRESS', 'in_progress_at': now})

    @action(detail=True, methods=['post'])
    def complete_work(self, request, pk=None):
        """Transitions request and assignment to COMPLETED"""
        service_request = self.get_object()
        now = timezone.now()
        service_request.status = ServiceRequest.Status.COMPLETED
        service_request.completed_at = now
        service_request.save(update_fields=['status', 'completed_at', 'updated_at'])

        active_assignment = service_request.assignments.filter(
            status__in=[Assignment.Status.ASSIGNED, Assignment.Status.ACCEPTED, Assignment.Status.IN_PROGRESS]
        ).first()
        if active_assignment:
            active_assignment.status = Assignment.Status.COMPLETED
            active_assignment.completed_at = now
            active_assignment.save(update_fields=['status', 'completed_at'])

        return Response({'status': 'COMPLETED', 'completed_at': now})

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopens request if resident marks issue as unresolved"""
        service_request = self.get_object()
        service_request.status = ServiceRequest.Status.REOPENED
        service_request.completed_at = None
        service_request.save(update_fields=['status', 'completed_at', 'updated_at'])
        
        # Trigger reassignment
        reason = request.data.get('reason', 'Resident reported issue was not resolved')
        assignment_service = AssignmentService()
        new_assignment, msg = assignment_service.reassign_request(service_request, reason=reason)

        return Response({
            'status': 'REOPENED',
            'message': msg,
            'new_assignment_id': str(new_assignment.id) if new_assignment else None
        })

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancels a service request"""
        service_request = self.get_object()
        service_request.status = ServiceRequest.Status.CANCELLED
        service_request.save(update_fields=['status', 'updated_at'])

        service_request.assignments.filter(
            status__in=[Assignment.Status.ASSIGNED, Assignment.Status.ACCEPTED, Assignment.Status.IN_PROGRESS]
        ).update(status=Assignment.Status.CANCELLED)

        return Response({'status': 'CANCELLED'})

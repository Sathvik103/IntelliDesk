from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from .models import Feedback
from .serializers import FeedbackSerializer
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment
from apps.ml_engine.service import AssignmentService

class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    filterset_fields = ['rating', 'is_resolved', 'met_sla', 'employee']
    ordering_fields = ['created_at', 'rating', 'resolution_time_minutes']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Feedback.objects.none()

        if user.is_superuser:
            return Feedback.objects.all().select_related('request', 'user', 'employee__user')

        if user.role == 'ADMIN':
            return Feedback.objects.filter(
                request__organization=user.organization
            ).select_related('request', 'user', 'employee__user')

        if user.role == 'EMPLOYEE':
            return Feedback.objects.filter(
                employee__user=user
            ).select_related('request', 'user', 'employee__user')

        return Feedback.objects.filter(
            user=user
        ).select_related('request', 'user', 'employee__user')

    def create(self, request, *args, **kwargs):
        request_id = request.data.get('request')
        if not request_id:
            return Response({'error': 'Request ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service_req = ServiceRequest.objects.get(id=request_id)
        except ServiceRequest.DoesNotExist:
            return Response({'error': 'Service request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if service_req.user != request.user and not request.user.is_superuser and request.user.role != 'ADMIN':
            return Response({'error': 'Only the requester can submit feedback.'}, status=status.HTTP_403_FORBIDDEN)

        if hasattr(service_req, 'feedback'):
            return Response({'error': 'Feedback already submitted for this request.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get completed assignment
        completed_assignment = service_req.assignments.filter(status=Assignment.Status.COMPLETED).first()
        if not completed_assignment:
            # Fallback to latest active assignment
            completed_assignment = service_req.assignments.first()

        if not completed_assignment:
            return Response({'error': 'No assigned workforce found for this request.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate resolution time and SLA met
        now = timezone.now()
        completed_time = service_req.completed_at or now
        created_time = service_req.created_at
        diff_seconds = (completed_time - created_time).total_seconds()
        resolution_mins = max(1, int(diff_seconds / 60))

        sla_minutes = service_req.domain.sla_hours * 60
        met_sla = resolution_mins <= sla_minutes

        is_resolved = request.data.get('is_resolved', True)
        if isinstance(is_resolved, str):
            is_resolved = is_resolved.lower() in ['true', '1', 'yes']

        rating = int(request.data.get('rating', 5))
        comments = request.data.get('comments', '')

        feedback = Feedback.objects.create(
            request=service_req,
            user=request.user,
            employee=completed_assignment.employee,
            is_resolved=is_resolved,
            rating=rating,
            comments=comments,
            resolution_time_minutes=resolution_mins,
            met_sla=met_sla
        )

        # If resident marked as unresolved, trigger automatic reopening and reassignment
        if not is_resolved:
            service_req.status = ServiceRequest.Status.REOPENED
            service_req.completed_at = None
            service_req.save(update_fields=['status', 'completed_at', 'updated_at'])
            assignment_service = AssignmentService()
            assignment_service.reassign_request(
                service_req,
                reason=f"Customer Feedback: Issue not resolved ({comments})"
            )

        serializer = self.get_serializer(feedback)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

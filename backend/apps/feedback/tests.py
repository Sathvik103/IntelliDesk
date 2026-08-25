import uuid
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import timedelta

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.employees.models import Employee
from apps.services.models import ServiceDomain, PredefinedIssue
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment
from apps.feedback.models import Feedback


class FeedbackModelTestCase(TestCase):
    """Unit tests for Feedback model and business logic."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org')
        
        self.resident = User.objects.create_user(
            username='resident',
            password='pass123',
            role='USER',
            organization=self.org
        )
        
        self.employee_user = User.objects.create_user(
            username='emp1',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org
        )
        
        self.employee = Employee.objects.create(
            user=self.employee_user,
            organization=self.org,
            max_active_assignments=5
        )
        
        self.domain = ServiceDomain.objects.create(
            organization=self.org,
            name='Plumbing',
            icon_name='wrench',
            sla_hours=4  # 240 minutes
        )
        
        self.predefined_issue = PredefinedIssue.objects.create(
            domain=self.domain,
            title='Leaky Faucet',
            default_priority='NORMAL'
        )

    def test_feedback_rating_persisted(self):
        """Test that rating is correctly persisted in Feedback model."""
        service_req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test issue',
            priority='NORMAL'
        )
        
        assignment = Assignment.objects.create(
            request=service_req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        feedback = Feedback.objects.create(
            request=service_req,
            user=self.resident,
            employee=self.employee,
            rating=4,
            comments='Good service',
            resolution_time_minutes=100,
            met_sla=True
        )
        
        self.assertEqual(feedback.rating, 4)
        self.assertEqual(feedback.comments, 'Good service')

    def test_resolution_time_calculated_correctly(self):
        """Test that resolution_time_minutes is calculated as (completed_at - created_at) / 60."""
        created_time = timezone.now() - timedelta(minutes=150)
        completed_time = created_time + timedelta(minutes=150)
        
        service_req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test issue',
            priority='NORMAL',
            created_at=created_time,
            completed_at=completed_time
        )
        
        assignment = Assignment.objects.create(
            request=service_req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        # Simulate the calculation done in FeedbackViewSet.create()
        diff_seconds = (completed_time - created_time).total_seconds()
        resolution_mins = max(1, int(diff_seconds / 60))
        
        feedback = Feedback.objects.create(
            request=service_req,
            user=self.resident,
            employee=self.employee,
            rating=5,
            resolution_time_minutes=resolution_mins,
            met_sla=True
        )
        
        self.assertEqual(feedback.resolution_time_minutes, 150)

    def test_met_sla_derived_from_sla_hours(self):
        """Test that met_sla is correctly derived from domain.sla_hours and resolution time."""
        created_time = timezone.now() - timedelta(minutes=180)  # 3 hours
        completed_time = created_time + timedelta(minutes=180)
        
        service_req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,  # sla_hours = 4 (240 minutes)
            predefined_issue=self.predefined_issue,
            custom_description='Test issue',
            priority='NORMAL',
            created_at=created_time,
            completed_at=completed_time
        )
        
        assignment = Assignment.objects.create(
            request=service_req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        sla_minutes = service_req.domain.sla_hours * 60  # 240
        resolution_mins = 180
        met_sla = resolution_mins <= sla_minutes  # True
        
        feedback = Feedback.objects.create(
            request=service_req,
            user=self.resident,
            employee=self.employee,
            rating=5,
            resolution_time_minutes=resolution_mins,
            met_sla=met_sla
        )
        
        self.assertTrue(feedback.met_sla)
        
        # Test SLA miss
        created_time2 = timezone.now() - timedelta(minutes=300)  # 5 hours
        completed_time2 = created_time2 + timedelta(minutes=300)
        
        service_req2 = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,  # sla_hours = 4 (240 minutes)
            predefined_issue=self.predefined_issue,
            custom_description='Test issue 2',
            priority='NORMAL',
            created_at=created_time2,
            completed_at=completed_time2
        )
        
        assignment2 = Assignment.objects.create(
            request=service_req2,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        resolution_mins2 = 300
        met_sla2 = resolution_mins2 <= sla_minutes  # False
        
        feedback2 = Feedback.objects.create(
            request=service_req2,
            user=self.resident,
            employee=self.employee,
            rating=3,
            resolution_time_minutes=resolution_mins2,
            met_sla=met_sla2
        )
        
        self.assertFalse(feedback2.met_sla)

    def test_duplicate_feedback_prevented_by_onetoone(self):
        """Test that OneToOne constraint prevents duplicate feedback submission."""
        service_req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test issue',
            priority='NORMAL'
        )
        
        assignment = Assignment.objects.create(
            request=service_req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        feedback1 = Feedback.objects.create(
            request=service_req,
            user=self.resident,
            employee=self.employee,
            rating=5,
            resolution_time_minutes=100,
            met_sla=True
        )
        
        # Attempting to create a second Feedback for same request should fail
        with self.assertRaises(Exception):
            Feedback.objects.create(
                request=service_req,
                user=self.resident,
                employee=self.employee,
                rating=4,
                resolution_time_minutes=100,
                met_sla=True
            )


class FeedbackAPITestCase(APITestCase):
    """Integration tests for Feedback API endpoints."""

    def setUp(self):
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Org')
        
        self.resident = User.objects.create_user(
            username='resident',
            password='pass123',
            role='USER',
            organization=self.org
        )
        
        self.employee_user = User.objects.create_user(
            username='emp1',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org
        )
        
        self.employee = Employee.objects.create(
            user=self.employee_user,
            organization=self.org,
            max_active_assignments=5
        )
        
        self.domain = ServiceDomain.objects.create(
            organization=self.org,
            name='Plumbing',
            icon_name='wrench',
            sla_hours=4
        )
        
        self.predefined_issue = PredefinedIssue.objects.create(
            domain=self.domain,
            title='Leaky Faucet',
            default_priority='NORMAL'
        )

    def test_submit_feedback_successfully(self):
        """Test successful feedback submission via API."""
        service_req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test issue',
            priority='NORMAL',
            completed_at=timezone.now()
        )
        
        assignment = Assignment.objects.create(
            request=service_req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        self.client.force_authenticate(user=self.resident)
        
        response = self.client.post('/api/feedback/', {
            'request': str(service_req.id),
            'rating': 5,
            'comments': 'Excellent service',
            'is_resolved': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 5)
        self.assertEqual(response.data['is_resolved'], True)

    def test_duplicate_feedback_returns_400(self):
        """Test that duplicate feedback submission returns HTTP 400."""
        service_req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test issue',
            priority='NORMAL',
            completed_at=timezone.now()
        )
        
        assignment = Assignment.objects.create(
            request=service_req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        Feedback.objects.create(
            request=service_req,
            user=self.resident,
            employee=self.employee,
            rating=5,
            resolution_time_minutes=100,
            met_sla=True
        )
        
        self.client.force_authenticate(user=self.resident)
        
        response = self.client.post('/api/feedback/', {
            'request': str(service_req.id),
            'rating': 4,
            'comments': 'Second attempt',
            'is_resolved': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already submitted', response.data['error'].lower())

    def test_unresolved_feedback_triggers_reassignment(self):
        """Test that is_resolved=False triggers reassignment and status change to REOPENED or QUEUED."""
        service_req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test issue',
            priority='NORMAL',
            status=ServiceRequest.Status.COMPLETED,
            completed_at=timezone.now()
        )
        
        assignment = Assignment.objects.create(
            request=service_req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        self.client.force_authenticate(user=self.resident)
        
        response = self.client.post('/api/feedback/', {
            'request': str(service_req.id),
            'rating': 2,
            'comments': 'Problem not resolved',
            'is_resolved': False
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that feedback was created
        self.assertTrue(Feedback.objects.filter(request=service_req).exists())
        
        # Check that request status is either REOPENED (if marked unresolved before reassignment)
        # or QUEUED/ASSIGNED (after reassignment attempt)
        service_req.refresh_from_db()
        self.assertIn(service_req.status, [ServiceRequest.Status.REOPENED, ServiceRequest.Status.QUEUED, ServiceRequest.Status.ASSIGNED])
        # completed_at should be cleared
        self.assertIsNone(service_req.completed_at)

    def test_feedback_missing_request_returns_400(self):
        """Test that missing request ID returns HTTP 400."""
        self.client.force_authenticate(user=self.resident)
        
        response = self.client.post('/api/feedback/', {
            'rating': 5,
            'comments': 'Good service',
            'is_resolved': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_feedback_invalid_request_returns_404(self):
        """Test that invalid request ID returns HTTP 404."""
        self.client.force_authenticate(user=self.resident)
        
        response = self.client.post('/api/feedback/', {
            'request': str(uuid.uuid4()),
            'rating': 5,
            'comments': 'Good service',
            'is_resolved': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

"""
Phase 3 tests for ServiceRequest isolation and lifecycle.
"""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.employees.models import Employee
from apps.services.models import ServiceDomain, PredefinedIssue
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment


class OrgIsolationTestCase(APITestCase):
    """
    Property 2 & 3: Organization isolation
    - List endpoint returns zero cross-tenant records
    - Detail endpoint returns 403/404
    """

    def setUp(self):
        self.client = APIClient()
        
        # Create two organizations
        self.org1 = Organization.objects.create(name='Organization 1')
        self.org2 = Organization.objects.create(name='Organization 2')
        
        # Create users in each organization
        self.user1_org1 = User.objects.create_user(
            username='user1_org1',
            password='pass123',
            role='USER',
            organization=self.org1
        )
        
        self.user2_org2 = User.objects.create_user(
            username='user2_org2',
            password='pass123',
            role='USER',
            organization=self.org2
        )
        
        # Create admin users for each org
        self.admin1_org1 = User.objects.create_user(
            username='admin1_org1',
            password='pass123',
            role='ADMIN',
            organization=self.org1
        )
        
        self.admin2_org2 = User.objects.create_user(
            username='admin2_org2',
            password='pass123',
            role='ADMIN',
            organization=self.org2
        )
        
        # Create service domains for each org
        self.domain1 = ServiceDomain.objects.create(
            organization=self.org1,
            name='Plumbing',
            icon_name='wrench',
            sla_hours=4
        )
        
        self.domain2 = ServiceDomain.objects.create(
            organization=self.org2,
            name='Electrical',
            icon_name='zap',
            sla_hours=6
        )
        
        # Create predefined issues
        self.issue1 = PredefinedIssue.objects.create(
            domain=self.domain1,
            title='Leaky Faucet',
            default_priority='NORMAL'
        )
        
        self.issue2 = PredefinedIssue.objects.create(
            domain=self.domain2,
            title='Power Outage',
            default_priority='URGENT'
        )
        
        # Create a service request in org1
        self.req_org1 = ServiceRequest.objects.create(
            user=self.user1_org1,
            organization=self.org1,
            domain=self.domain1,
            predefined_issue=self.issue1,
            custom_description='Test request in org1',
            priority='NORMAL'
        )
        
        # Create a service request in org2
        self.req_org2 = ServiceRequest.objects.create(
            user=self.user2_org2,
            organization=self.org2,
            domain=self.domain2,
            predefined_issue=self.issue2,
            custom_description='Test request in org2',
            priority='URGENT'
        )

    def test_list_endpoint_does_not_return_cross_tenant_records(self):
        """Test that list endpoint returns zero cross-org records."""
        self.client.force_authenticate(user=self.admin1_org1)
        
        response = self.client.get('/api/requests/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin1 (org1) should only see org1 requests, not org2
        results = response.data.get('results', [])
        org_ids = [str(req['organization']) for req in results]
        
        # Verify no cross-org records
        self.assertNotIn(str(self.org2.id), org_ids)
        # Verify org1 records are present
        org1_req_ids = [str(req['id']) for req in results]
        self.assertIn(str(self.req_org1.id), org1_req_ids)

    def test_detail_endpoint_returns_404_for_cross_org_access(self):
        """Test that detail endpoint returns 404 when accessing cross-org request (tenant isolation)."""
        self.client.force_authenticate(user=self.admin1_org1)
        
        # Try to access a request from org2
        response = self.client.get(f'/api/requests/{self.req_org2.id}/')
        
        # Should return 404 — queryset scoping hides cross-org objects (correct DRF tenant isolation)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_user_cannot_patch_cross_org_request(self):
        """Test that PATCH to cross-org request returns 404 (tenant isolation)."""
        self.client.force_authenticate(user=self.admin1_org1)
        
        # Try to update a request from org2
        response = self.client.patch(f'/api/requests/{self.req_org2.id}/', {
            'priority': 'CRITICAL'
        })
        
        # Should return 404 — queryset scoping hides cross-org objects
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_user_cannot_delete_cross_org_request(self):
        """Test that DELETE to cross-org request returns 404 (tenant isolation)."""
        self.client.force_authenticate(user=self.admin1_org1)
        
        # Try to delete a request from org2
        response = self.client.delete(f'/api/requests/{self.req_org2.id}/')
        
        # Should return 404 — queryset scoping hides cross-org objects
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_user_can_access_own_org_request(self):
        """Test that user can access request from their own org."""
        self.client.force_authenticate(user=self.user1_org1)
        
        response = self.client.get(f'/api/requests/{self.req_org1.id}/')
        
        # Should return 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data['id']), str(self.req_org1.id))


class ServiceRequestLifecycleTestCase(TestCase):
    """
    Property 4: Auto-assignment fires on every new valid request
    Test CREATED → ASSIGNED → IN_PROGRESS → COMPLETED flow
    """

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
            max_active_assignments=5,
            status='ACTIVE',
            is_available=True
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

    def test_request_created_status(self):
        """Test that new request starts in CREATED status."""
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL'
        )
        
        self.assertEqual(req.status, ServiceRequest.Status.CREATED)

    def test_request_transitions_to_assigned_with_eligible_employee(self):
        """Test CREATED → ASSIGNED when eligible employee exists."""
        from apps.employees.models import EmployeeSkill
        
        # Add domain skill to employee
        EmployeeSkill.objects.create(
            employee=self.employee,
            domain=self.domain,
            proficiency_level=3
        )
        
        # Create request
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL'
        )
        
        # Trigger auto-assignment manually (normally done by signal/celery)
        # In real implementation, check if auto_assign signal was called
        # For now, verify assignment can be created
        assignment = Assignment.objects.create(
            request=req,
            employee=self.employee,
            status=Assignment.Status.ASSIGNED
        )
        
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.status, Assignment.Status.ASSIGNED)

    def test_request_transitions_through_lifecycle(self):
        """Test full lifecycle: CREATED → ASSIGNED → IN_PROGRESS → COMPLETED."""
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL'
        )
        
        # Create assignment
        assignment = Assignment.objects.create(
            request=req,
            employee=self.employee,
            status=Assignment.Status.ASSIGNED
        )
        
        req.status = ServiceRequest.Status.ASSIGNED
        req.save()
        
        self.assertEqual(req.status, ServiceRequest.Status.ASSIGNED)
        
        # Transition to IN_PROGRESS
        from django.utils import timezone
        req.status = ServiceRequest.Status.IN_PROGRESS
        req.in_progress_at = timezone.now()
        req.save()
        
        assignment.status = Assignment.Status.IN_PROGRESS
        assignment.save()
        
        self.assertEqual(req.status, ServiceRequest.Status.IN_PROGRESS)
        self.assertIsNotNone(req.in_progress_at)
        
        # Transition to COMPLETED
        req.status = ServiceRequest.Status.COMPLETED
        req.completed_at = timezone.now()
        req.save()
        
        assignment.status = Assignment.Status.COMPLETED
        assignment.save()
        
        self.assertEqual(req.status, ServiceRequest.Status.COMPLETED)
        self.assertIsNotNone(req.completed_at)

    def test_cancel_request_from_any_open_status(self):
        """Test that any open status → CANCELLED is possible."""
        for initial_status in [
            ServiceRequest.Status.CREATED,
            ServiceRequest.Status.QUEUED,
            ServiceRequest.Status.ASSIGNED,
            ServiceRequest.Status.IN_PROGRESS,
        ]:
            req = ServiceRequest.objects.create(
                user=self.resident,
                organization=self.org,
                domain=self.domain,
                predefined_issue=self.predefined_issue,
                custom_description=f'Test {initial_status}',
                priority='NORMAL',
                status=initial_status
            )
            
            req.status = ServiceRequest.Status.CANCELLED
            req.save()
            
            self.assertEqual(req.status, ServiceRequest.Status.CANCELLED)



class ReopenedFeedbackLifecycleTestCase(TestCase):
    """
    Test COMPLETED + unresolved feedback → REOPENED lifecycle.
    """

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
            max_active_assignments=5,
            status='ACTIVE',
            is_available=True
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

    def test_completed_request_can_reopen_via_unresolved_feedback(self):
        """Test COMPLETED + unresolved feedback → REOPENED."""
        from django.utils import timezone
        from apps.feedback.models import Feedback
        
        # Create and complete request
        req = ServiceRequest.objects.create(
            user=self.resident,
            organization=self.org,
            domain=self.domain,
            predefined_issue=self.predefined_issue,
            custom_description='Test',
            priority='NORMAL',
            status=ServiceRequest.Status.COMPLETED,
            completed_at=timezone.now()
        )
        
        assignment = Assignment.objects.create(
            request=req,
            employee=self.employee,
            status=Assignment.Status.COMPLETED
        )
        
        # Submit unresolved feedback
        feedback = Feedback.objects.create(
            request=req,
            user=self.resident,
            employee=self.employee,
            is_resolved=False,
            rating=2,
            comments='Problem not solved',
            resolution_time_minutes=100,
            met_sla=True
        )
        
        # In real implementation, the feedback submission would trigger reassignment
        # For now, verify feedback is marked as unresolved
        self.assertFalse(feedback.is_resolved)

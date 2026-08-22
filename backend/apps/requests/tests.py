from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.services.models import ServiceDomain, PredefinedIssue
from apps.employees.models import Employee, EmployeeRole, EmployeeSkill
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment

class ServiceRequestApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(
            name="Emerald Heights",
            org_type=Organization.OrgType.RESIDENTIAL_COLONY,
            latitude=12.9304,
            longitude=77.6784
        )
        self.domain = ServiceDomain.objects.create(
            organization=self.org,
            name="Electrical",
            sla_hours=12
        )
        self.issue = PredefinedIssue.objects.create(
            domain=self.domain,
            title="Switch Sparking",
            default_priority=PredefinedIssue.Priority.HIGH
        )
        self.resident = User.objects.create_user(
            username="test_user",
            password="password123",
            organization=self.org,
            role=User.Role.USER
        )
        self.emp_user = User.objects.create_user(
            username="test_tech",
            password="password123",
            organization=self.org,
            role=User.Role.EMPLOYEE
        )
        self.emp = Employee.objects.create(
            user=self.emp_user,
            organization=self.org,
            experience_years=4,
            current_latitude=12.9305,
            current_longitude=77.6785,
            status=Employee.Status.ACTIVE,
            is_available=True
        )
        EmployeeSkill.objects.create(
            employee=self.emp,
            domain=self.domain,
            proficiency_level=4
        )

    def test_request_lifecycle_via_api(self):
        # 1. Login as resident
        self.client.force_authenticate(user=self.resident)

        # 2. Create service request
        response = self.client.post('/api/requests/', {
            'domain': str(self.domain.id),
            'predefined_issue': str(self.issue.id),
            'custom_description': 'Sparking in living room outlet',
            'location_name': 'Block B, Apt 304',
            'priority': 'HIGH',
            'latitude': 12.9304,
            'longitude': 77.6784
        }, format='json')

        self.assertEqual(response.status_code, 201)
        req_id = response.data['id']
        self.assertEqual(response.data['status'], 'ASSIGNED')
        self.assertIsNotNone(response.data['active_assignment'])

        # 3. Login as employee to start work
        self.client.force_authenticate(user=self.emp_user)
        start_res = self.client.post(f'/api/requests/{req_id}/start_work/')
        self.assertEqual(start_res.status_code, 200)
        self.assertEqual(start_res.data['status'], 'IN_PROGRESS')

        # 4. Complete work
        comp_res = self.client.post(f'/api/requests/{req_id}/complete_work/')
        self.assertEqual(comp_res.status_code, 200)
        self.assertEqual(comp_res.data['status'], 'COMPLETED')

        # 5. Login as resident to submit feedback
        self.client.force_authenticate(user=self.resident)
        fb_res = self.client.post('/api/feedback/', {
            'request': req_id,
            'is_resolved': True,
            'rating': 5,
            'comments': 'Technician fixed it swiftly!'
        }, format='json')
        self.assertEqual(fb_res.status_code, 201)
        self.assertEqual(fb_res.data['rating'], 5)
        self.assertTrue(fb_res.data['is_resolved'])

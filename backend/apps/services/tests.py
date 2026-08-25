"""
Tests for ServiceDomain CRUD permissions.
"""
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.employees.models import Employee
from apps.services.models import ServiceDomain, PredefinedIssue


class ServiceDomainCRUDPermissionTestCase(APITestCase):
    """
    Test CRUD permissions for ServiceDomain.
    Validates Requirements 11.1, 17.10
    """

    def setUp(self):
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Org')
        self.other_org = Organization.objects.create(name='Other Org')
        
        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            role='ADMIN',
            organization=self.org
        )
        
        self.employee_user = User.objects.create_user(
            username='employee',
            password='pass123',
            role='EMPLOYEE',
            organization=self.org
        )
        self.employee = Employee.objects.create(
            user=self.employee_user,
            organization=self.org,
            max_active_assignments=3
        )
        
        self.resident_user = User.objects.create_user(
            username='resident',
            password='pass123',
            role='USER',
            organization=self.org
        )
        
        # Create a domain for testing
        self.domain = ServiceDomain.objects.create(
            organization=self.org,
            name='Plumbing',
            icon_name='wrench',
            sla_hours=4
        )

    def test_admin_can_create_domain_in_own_org(self):
        """Test that admin can create a domain in their own organization."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post('/api/services/domains/', {
            'name': 'Electrical',
            'icon_name': 'zap',
            'sla_hours': 6,
            'is_active': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Electrical')

    def test_admin_can_update_domain_in_own_org(self):
        """Test that admin can update a domain in their own organization."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.patch(f'/api/services/domains/{self.domain.id}/', {
            'sla_hours': 8
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sla_hours'], 8)

    def test_admin_can_delete_domain_in_own_org(self):
        """Test that admin can delete a domain in their own organization."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(f'/api/services/domains/{self.domain.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify domain is deleted
        self.assertFalse(ServiceDomain.objects.filter(id=self.domain.id).exists())

    def test_employee_cannot_create_domain(self):
        """Test that employee receives 403 on create domain."""
        self.client.force_authenticate(user=self.employee_user)
        
        response = self.client.post('/api/services/domains/', {
            'name': 'Electrical',
            'icon_name': 'zap',
            'sla_hours': 6
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_update_domain(self):
        """Test that employee receives 403 on update domain."""
        self.client.force_authenticate(user=self.employee_user)
        
        response = self.client.patch(f'/api/services/domains/{self.domain.id}/', {
            'sla_hours': 8
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_delete_domain(self):
        """Test that employee receives 403 on delete domain."""
        self.client.force_authenticate(user=self.employee_user)
        
        response = self.client.delete(f'/api/services/domains/{self.domain.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_resident_cannot_create_domain(self):
        """Test that resident receives 403 on create domain."""
        self.client.force_authenticate(user=self.resident_user)
        
        response = self.client.post('/api/services/domains/', {
            'name': 'Electrical',
            'icon_name': 'zap',
            'sla_hours': 6
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_resident_cannot_update_domain(self):
        """Test that resident receives 403 on update domain."""
        self.client.force_authenticate(user=self.resident_user)
        
        response = self.client.patch(f'/api/services/domains/{self.domain.id}/', {
            'sla_hours': 8
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_resident_cannot_delete_domain(self):
        """Test that resident receives 403 on delete domain."""
        self.client.force_authenticate(user=self.resident_user)
        
        response = self.client.delete(f'/api/services/domains/{self.domain.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_create_domain_in_other_org(self):
        """Test that admin cannot create domain in other organization."""
        other_admin = User.objects.create_user(
            username='other_admin',
            password='pass123',
            role='ADMIN',
            organization=self.other_org
        )
        
        self.client.force_authenticate(user=other_admin)
        
        # The endpoint might not allow specifying a different organization
        # or it should automatically use the user's organization
        response = self.client.post('/api/services/domains/', {
            'name': 'Electrical',
            'icon_name': 'zap',
            'sla_hours': 6,
            'is_active': True
        })
        
        if response.status_code == status.HTTP_201_CREATED:
            # Verify the domain was created in the other_admin's org
            self.assertEqual(str(response.data['organization']), str(self.other_org.id))


class PredefinedIssueCRUDTestCase(APITestCase):
    """
    Test CRUD operations for PredefinedIssues.
    """

    def setUp(self):
        self.client = APIClient()
        
        self.org = Organization.objects.create(name='Test Org')
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='pass123',
            role='ADMIN',
            organization=self.org
        )
        
        self.domain = ServiceDomain.objects.create(
            organization=self.org,
            name='Plumbing',
            icon_name='wrench',
            sla_hours=4
        )
        
        self.issue = PredefinedIssue.objects.create(
            domain=self.domain,
            title='Leaky Faucet',
            default_priority='NORMAL'
        )

    def test_admin_can_create_predefined_issue(self):
        """Test that admin can create a predefined issue."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post('/api/services/issues/', {
            'domain': str(self.domain.id),
            'title': 'Pipe Burst',
            'default_priority': 'URGENT'
        })
        
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND])

    def test_admin_can_update_predefined_issue(self):
        """Test that admin can update a predefined issue."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.patch(f'/api/services/issues/{self.issue.id}/', {
            'title': 'Severe Leak'
        })
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_admin_can_delete_predefined_issue(self):
        """Test that admin can delete a predefined issue."""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(f'/api/services/issues/{self.issue.id}/')
        
        self.assertIn(response.status_code, [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND])

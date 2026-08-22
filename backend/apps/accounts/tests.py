from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User


def make_org(name='Org'):
    return Organization.objects.create(name=name, org_type='RESIDENTIAL_COLONY')


def make_user(org, username='u', role='USER'):
    return User.objects.create_user(
        username=username, password='pass1234',
        email=f'{username}@test.com', role=role, organization=org
    )


class UserPermissionTest(TestCase):
    """Residents/employees cannot manage users; only admins can."""

    def setUp(self):
        self.org = make_org('UserPermOrg')
        self.admin = make_user(self.org, 'upm_admin', 'ADMIN')
        self.resident = make_user(self.org, 'upm_res', 'USER')
        self.employee = make_user(self.org, 'upm_emp', 'EMPLOYEE')
        self.client = APIClient()

    def test_resident_cannot_list_users(self):
        self.client.force_authenticate(self.resident)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_list_users(self):
        self.client.force_authenticate(self.employee)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_admin_can_create_user(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/auth/users/', {
            'username': 'new_employee',
            'email': 'emp@test.com',
            'password': 'pass1234',
            'role': 'EMPLOYEE',
            'first_name': 'New',
            'last_name': 'Employee',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        new_user = User.objects.get(username='new_employee')
        # org should be auto-assigned to admin's org
        self.assertEqual(new_user.organization, self.org)


class UserOrgIsolationTest(TestCase):
    """Admin from Org A cannot see or touch users from Org B."""

    def setUp(self):
        self.org_a = make_org('OrgA Isolate')
        self.org_b = make_org('OrgB Isolate')
        self.admin_a = make_user(self.org_a, 'isol_admin_a', 'ADMIN')
        self.user_b = make_user(self.org_b, 'isol_user_b', 'USER')
        self.client = APIClient()
        self.client.force_authenticate(self.admin_a)

    def test_admin_cannot_see_other_org_user(self):
        resp = self.client.get('/api/auth/users/')
        self.assertEqual(resp.status_code, 200)
        ids = [str(u['id']) for u in resp.data.get('results', [])]
        self.assertNotIn(str(self.user_b.id), ids)

    def test_admin_cannot_modify_other_org_user(self):
        resp = self.client.patch(f'/api/auth/users/{self.user_b.id}/', {'first_name': 'Hacked'})
        self.assertIn(resp.status_code, [403, 404])


class UserActivationTest(TestCase):
    """Admin can activate and deactivate users."""

    def setUp(self):
        self.org = make_org('ActOrg')
        self.admin = make_user(self.org, 'act_admin', 'ADMIN')
        self.target = make_user(self.org, 'act_target', 'USER')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_deactivate_user(self):
        resp = self.client.post(f'/api/auth/users/{self.target.id}/deactivate/')
        self.assertEqual(resp.status_code, 200)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_activate_user(self):
        self.target.is_active = False
        self.target.save()
        resp = self.client.post(f'/api/auth/users/{self.target.id}/activate/')
        self.assertEqual(resp.status_code, 200)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_admin_cannot_deactivate_self(self):
        resp = self.client.post(f'/api/auth/users/{self.admin.id}/deactivate/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class RegisterRoleRestrictionTest(TestCase):
    """Self-registration cannot create ADMIN or EMPLOYEE accounts."""

    def setUp(self):
        self.client = APIClient()
        make_org('RegOrg')

    def test_register_admin_role_rejected(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'hacker', 'password': 'pass1234',
            'email': 'h@test.com', 'role': 'ADMIN',
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_employee_role_rejected(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'emp_sneaky', 'password': 'pass1234',
            'email': 'e@test.com', 'role': 'EMPLOYEE',
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_resident_succeeds(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'new_resident', 'password': 'pass1234',
            'email': 'r@test.com', 'role': 'USER',
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

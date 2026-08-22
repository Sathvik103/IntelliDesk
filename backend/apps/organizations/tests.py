from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User


def make_org(name='Org A', org_type='RESIDENTIAL_COLONY'):
    return Organization.objects.create(name=name, org_type=org_type)


def make_admin(org, username='admin_a'):
    u = User.objects.create_user(
        username=username, password='pass1234',
        email=f'{username}@test.com', role='ADMIN', organization=org
    )
    return u


def make_resident(org, username='resident_a'):
    u = User.objects.create_user(
        username=username, password='pass1234',
        email=f'{username}@test.com', role='USER', organization=org
    )
    return u


class OrganizationPermissionTest(TestCase):
    """Anonymous and resident cannot write; admin can."""

    def setUp(self):
        self.org = make_org('TestOrg')
        self.admin = make_admin(self.org, 'adm1')
        self.resident = make_resident(self.org, 'res1')
        self.client = APIClient()

    def _url_list(self):
        return '/api/organizations/'

    def _url_detail(self, pk):
        return f'/api/organizations/{pk}/'

    def test_anonymous_list_returns_401(self):
        resp = self.client.get(self._url_list())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_create_returns_401(self):
        resp = self.client.post(self._url_list(), {'name': 'Hack'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_resident_list_returns_200(self):
        self.client.force_authenticate(self.resident)
        resp = self.client.get(self._url_list())
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_resident_create_returns_403(self):
        self.client.force_authenticate(self.resident)
        resp = self.client.post(self._url_list(), {'name': 'Sneaky', 'org_type': 'OTHER'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_own_org(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.patch(self._url_detail(str(self.org.id)), {'name': 'Updated Org'})
        self.assertIn(resp.status_code, [200, 201])
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, 'Updated Org')


class OrganizationIsolationTest(TestCase):
    """Admin of Org A cannot see or modify Org B."""

    def setUp(self):
        self.org_a = make_org('Org Alpha')
        self.org_b = make_org('Org Beta')
        self.admin_a = make_admin(self.org_a, 'admin_alpha')
        self.client = APIClient()

    def test_admin_sees_only_own_org(self):
        self.client.force_authenticate(self.admin_a)
        resp = self.client.get('/api/organizations/')
        self.assertEqual(resp.status_code, 200)
        ids = [str(o['id']) for o in resp.data['results'] if 'id' in o]
        self.assertIn(str(self.org_a.id), ids)
        self.assertNotIn(str(self.org_b.id), ids)

    def test_admin_cannot_modify_other_org(self):
        self.client.force_authenticate(self.admin_a)
        resp = self.client.patch(f'/api/organizations/{self.org_b.id}/', {'name': 'Hijacked'})
        # Either 403 or 404 is acceptable — object not in queryset
        self.assertIn(resp.status_code, [403, 404])


class OrganizationActivateDeactivateTest(TestCase):
    """Admin can activate and deactivate an org."""

    def setUp(self):
        self.org = make_org('ActiveOrg')
        self.admin = make_admin(self.org, 'act_admin')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_deactivate_and_activate(self):
        resp = self.client.post(f'/api/organizations/{self.org.id}/deactivate/')
        self.assertEqual(resp.status_code, 200)
        self.org.refresh_from_db()
        self.assertFalse(self.org.is_active)

        resp = self.client.post(f'/api/organizations/{self.org.id}/activate/')
        self.assertEqual(resp.status_code, 200)
        self.org.refresh_from_db()
        self.assertTrue(self.org.is_active)


class OrgTypesEndpointTest(TestCase):
    """org_types action returns valid choices."""

    def setUp(self):
        self.org = make_org()
        self.user = make_resident(self.org)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_org_types_returns_list(self):
        resp = self.client.get('/api/organizations/org_types/')
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.data, list)
        values = [item['value'] for item in resp.data]
        self.assertIn('RESIDENTIAL_COLONY', values)
        self.assertIn('GATED_COMMUNITY', values)

from datetime import time
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.employees.models import Employee, EmployeeRole, EmployeeSkill, EmployeeSchedule
from apps.services.models import ServiceDomain


def make_org(name='EmpOrg'):
    return Organization.objects.create(name=name, org_type='RESIDENTIAL_COLONY')


def make_user(org, username='u', role='USER'):
    return User.objects.create_user(
        username=username, password='pass1234',
        email=f'{username}@test.com', role=role, organization=org
    )


def make_role(org, title='Technician'):
    return EmployeeRole.objects.create(organization=org, title=title)


def make_employee(org, role=None, username='emp_x'):
    u = make_user(org, username, 'EMPLOYEE')
    emp = Employee.objects.create(
        user=u, organization=org, role=role,
        experience_years=3, max_active_assignments=3,
        current_latitude=12.9, current_longitude=77.6,
    )
    return emp


def make_domain(org, name='Electrical'):
    return ServiceDomain.objects.create(organization=org, name=name, sla_hours=24)


class EmployeeCRUDPermissionTest(TestCase):
    """Residents cannot modify employees; admin can."""

    def setUp(self):
        self.org = make_org('CRUDOrg')
        self.admin = make_user(self.org, 'crud_admin', 'ADMIN')
        self.resident = make_user(self.org, 'crud_res', 'USER')
        self.role = make_role(self.org, 'Electrician')
        self.emp = make_employee(self.org, self.role, 'crud_emp')
        self.client = APIClient()

    def test_resident_cannot_create_employee(self):
        self.client.force_authenticate(self.resident)
        resp = self.client.post('/api/employees/', {})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_resident_can_list_employees(self):
        self.client.force_authenticate(self.resident)
        resp = self.client.get('/api/employees/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_admin_can_set_status(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/employees/{self.emp.id}/set_status/', {'status': 'ON_LEAVE'}
        )
        self.assertEqual(resp.status_code, 200)
        self.emp.refresh_from_db()
        self.assertEqual(self.emp.status, 'ON_LEAVE')

    def test_set_status_inactive_clears_availability(self):
        self.client.force_authenticate(self.admin)
        self.emp.is_available = True
        self.emp.save()
        resp = self.client.post(
            f'/api/employees/{self.emp.id}/set_status/', {'status': 'INACTIVE'}
        )
        self.assertEqual(resp.status_code, 200)
        self.emp.refresh_from_db()
        self.assertFalse(self.emp.is_available)

    def test_invalid_status_returns_400(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post(
            f'/api/employees/{self.emp.id}/set_status/', {'status': 'FLYING'}
        )
        self.assertEqual(resp.status_code, 400)


class EmployeeOrgIsolationTest(TestCase):
    """Admin from Org A cannot touch employees in Org B."""

    def setUp(self):
        self.org_a = make_org('EmpOrgA')
        self.org_b = make_org('EmpOrgB')
        self.admin_a = make_user(self.org_a, 'emp_iso_admin', 'ADMIN')
        self.emp_b = make_employee(self.org_b, username='emp_in_b')
        self.client = APIClient()
        self.client.force_authenticate(self.admin_a)

    def test_admin_cannot_see_other_org_employee(self):
        resp = self.client.get('/api/employees/')
        ids = [str(e['id']) for e in resp.data.get('results', [])]
        self.assertNotIn(str(self.emp_b.id), ids)

    def test_admin_cannot_modify_other_org_employee(self):
        resp = self.client.post(
            f'/api/employees/{self.emp_b.id}/set_status/', {'status': 'INACTIVE'}
        )
        self.assertIn(resp.status_code, [403, 404])


class EmployeeSkillTest(TestCase):
    """Employee can have multiple skills at different proficiency levels."""

    def setUp(self):
        self.org = make_org('SkillOrg')
        self.admin = make_user(self.org, 'skill_admin', 'ADMIN')
        self.emp = make_employee(self.org, username='skill_emp')
        self.domain1 = make_domain(self.org, 'Electrical')
        self.domain2 = make_domain(self.org, 'Plumbing')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_admin_can_add_skills(self):
        resp = self.client.post('/api/employees/skills/', {
            'employee': str(self.emp.id),
            'domain': str(self.domain1.id),
            'proficiency_level': 4,
            'years_of_experience': 2,
        })
        self.assertEqual(resp.status_code, 201)

    def test_employee_can_have_multiple_skills(self):
        self.client.post('/api/employees/skills/', {
            'employee': str(self.emp.id),
            'domain': str(self.domain1.id),
            'proficiency_level': 4,
            'years_of_experience': 2,
        })
        self.client.post('/api/employees/skills/', {
            'employee': str(self.emp.id),
            'domain': str(self.domain2.id),
            'proficiency_level': 2,
            'years_of_experience': 1,
        })
        self.assertEqual(self.emp.skills.count(), 2)

    def test_duplicate_domain_skill_rejected(self):
        self.client.post('/api/employees/skills/', {
            'employee': str(self.emp.id),
            'domain': str(self.domain1.id),
            'proficiency_level': 3,
            'years_of_experience': 1,
        })
        resp = self.client.post('/api/employees/skills/', {
            'employee': str(self.emp.id),
            'domain': str(self.domain1.id),
            'proficiency_level': 5,
            'years_of_experience': 5,
        })
        # Model has unique constraint on (employee, domain)
        self.assertIn(resp.status_code, [400, 409])

    def test_resident_cannot_add_skills(self):
        resident = make_user(self.org, 'skill_res', 'USER')
        self.client.force_authenticate(resident)
        resp = self.client.post('/api/employees/skills/', {
            'employee': str(self.emp.id),
            'domain': str(self.domain1.id),
            'proficiency_level': 3,
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class EmployeeRolePermissionTest(TestCase):
    """Only admin can create/update/delete roles."""

    def setUp(self):
        self.org = make_org('RoleOrg')
        self.admin = make_user(self.org, 'role_admin', 'ADMIN')
        self.resident = make_user(self.org, 'role_res', 'USER')
        self.client = APIClient()

    def test_resident_cannot_create_role(self):
        self.client.force_authenticate(self.resident)
        resp = self.client.post('/api/employees/roles/', {'title': 'Hacker Role'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_role(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/employees/roles/', {
            'title': 'Senior Electrician',
            'description': 'Handles HV installations',
        })
        self.assertEqual(resp.status_code, 201, msg=f"Create role error: {resp.data}")
        self.assertEqual(EmployeeRole.objects.filter(organization=self.org).count(), 1)


class EmployeeScheduleTest(TestCase):
    """is_on_schedule returns correct result based on time/day."""

    def setUp(self):
        self.org = make_org('SchedOrg')
        self.admin = make_user(self.org, 'sched_admin', 'ADMIN')
        self.emp = make_employee(self.org, username='sched_emp')
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_create_schedule_entry(self):
        now = timezone.localtime(timezone.now())
        resp = self.client.post('/api/employees/schedules/', {
            'employee': str(self.emp.id),
            'day_of_week': now.weekday(),
            'start_time': '00:00:00',
            'end_time': '23:59:59',
            'is_active': True,
        })
        self.assertEqual(resp.status_code, 201)

    def test_is_on_schedule_true_when_within_hours(self):
        now = timezone.localtime(timezone.now())
        # Create a schedule covering the full day today
        EmployeeSchedule.objects.create(
            employee=self.emp,
            day_of_week=now.weekday(),
            start_time=time(0, 0, 0),
            end_time=time(23, 59, 59),
            is_active=True,
        )
        resp = self.client.get(f'/api/employees/{self.emp.id}/is_on_schedule/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['on_schedule'])

    def test_is_on_schedule_false_when_no_active_schedule(self):
        # No schedules at all
        resp = self.client.get(f'/api/employees/{self.emp.id}/is_on_schedule/')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['on_schedule'])

    def test_duplicate_schedule_day_rejected(self):
        now = timezone.localtime(timezone.now())
        self.client.post('/api/employees/schedules/', {
            'employee': str(self.emp.id),
            'day_of_week': now.weekday(),
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'is_active': True,
        })
        resp = self.client.post('/api/employees/schedules/', {
            'employee': str(self.emp.id),
            'day_of_week': now.weekday(),
            'start_time': '10:00:00',
            'end_time': '18:00:00',
            'is_active': True,
        })
        self.assertIn(resp.status_code, [400, 409])


class EmployeeFilterTest(TestCase):
    """Search, filter, and pagination work correctly."""

    def setUp(self):
        self.org = make_org('FilterOrg')
        self.admin = make_user(self.org, 'filter_admin', 'ADMIN')
        self.role = make_role(self.org, 'Plumber')
        self.emp1 = make_employee(self.org, self.role, 'filter_emp1')
        self.emp1.status = 'ACTIVE'
        self.emp1.is_available = True
        self.emp1.save()
        self.emp2 = make_employee(self.org, self.role, 'filter_emp2')
        self.emp2.status = 'ON_LEAVE'
        self.emp2.is_available = False
        self.emp2.save()
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_filter_by_status(self):
        resp = self.client.get('/api/employees/?status=ACTIVE')
        self.assertEqual(resp.status_code, 200)
        statuses = [e['status'] for e in resp.data.get('results', [])]
        self.assertTrue(all(s == 'ACTIVE' for s in statuses))

    def test_filter_by_availability(self):
        resp = self.client.get('/api/employees/?is_available=false')
        self.assertEqual(resp.status_code, 200)
        avails = [e['is_available'] for e in resp.data.get('results', [])]
        self.assertTrue(all(a == False for a in avails))

    def test_search_by_name(self):
        self.emp1.user.first_name = 'Rajesh'
        self.emp1.user.save()
        resp = self.client.get('/api/employees/?search=Rajesh')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.data.get('results', [])), 0)

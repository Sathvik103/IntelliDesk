"""
Idempotent Django management command to populate the database with realistic demo data.

This command creates:
1. Organizations (Green Valley Residency, Sunrise Colony, TechPark Business Center)
2. Users (superadmin, org admins, 4 residents per org, 5 employees per org)
3. Service domains (8 per org) and predefined issues (5–6 per domain)
4. Employee profiles with roles, skills, and schedules
5. Historical service requests (15 completed, 5 active, 3 urgent) with feedback

All operations use get_or_create for idempotency: running multiple times produces
the same database state as running once.
"""

import random
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.employees.models import Employee, EmployeeRole, EmployeeSchedule, EmployeeSkill
from apps.feedback.models import Feedback
from apps.organizations.models import Organization
from apps.requests.models import ServiceRequest
from apps.services.models import PredefinedIssue, ServiceDomain


class Command(BaseCommand):
    help = "Seed the database with realistic demo data (idempotent)"

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write(self.style.SUCCESS("\n=== Starting Database Seeding ===\n"))

                # Task 2.2: Organizations, users, admins, residents
                self.stdout.write("\n--- Task 2.2: Creating organizations, users, and admins ---")
                orgs = self._seed_organizations()
                self._seed_superadmin()
                self._seed_org_admins(orgs)
                residents_by_org = self._seed_residents(orgs)
                self._seed_employee_users(orgs)

                # Task 2.3: Service domains and predefined issues
                self.stdout.write("\n--- Task 2.3: Creating service domains and predefined issues ---")
                self._seed_service_domains_and_issues(orgs)

                # Task 2.4: Employee profiles, skills, schedules
                self.stdout.write("\n--- Task 2.4: Creating employee profiles, skills, and schedules ---")
                self._seed_employee_profiles(orgs)

                # Task 2.5: Historical requests and feedback
                self.stdout.write("\n--- Task 2.5: Creating historical requests and feedback ---")
                self._seed_historical_requests(orgs, residents_by_org)

                self.stdout.write(self.style.SUCCESS("\n=== Database Seeding Complete ===\n"))
                self._print_counts()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n!!! ERROR during seeding: {e}\n"))
            raise

    # ─────────────────────────────────────────────────────────────────
    # Task 2.2 helpers
    # ─────────────────────────────────────────────────────────────────

    def _seed_organizations(self):
        """Create 3 organizations with exact spec data."""
        org_data = [
            {
                "name": "Green Valley Residency",
                "org_type": Organization.OrgType.GATED_COMMUNITY,
                "address": "Sector 62, Noida, UP",
                "latitude": Decimal("28.6272"),
                "longitude": Decimal("77.3666"),
                "contact_email": "admin@greenvalley.in",
                "contact_phone": "+91-120-4567890",
            },
            {
                "name": "Sunrise Colony",
                "org_type": Organization.OrgType.RESIDENTIAL_COLONY,
                "address": "Rohini Sector 15, Delhi",
                "latitude": Decimal("28.7041"),
                "longitude": Decimal("77.1025"),
                "contact_email": "admin@sunrisecolony.in",
                "contact_phone": "+91-11-45678901",
            },
            {
                "name": "TechPark Business Center",
                "org_type": Organization.OrgType.OFFICE_SPACE,
                "address": "Koramangala 6th Block, Bengaluru",
                "latitude": Decimal("12.9352"),
                "longitude": Decimal("77.6245"),
                "contact_email": "admin@techpark.in",
                "contact_phone": "+91-80-45678902",
            },
        ]

        orgs = {}
        for data in org_data:
            org, created = Organization.objects.get_or_create(
                name=data["name"],
                defaults={
                    "org_type": data["org_type"],
                    "address": data["address"],
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "contact_email": data["contact_email"],
                    "contact_phone": data["contact_phone"],
                    "is_active": True,
                },
            )
            orgs[data["name"]] = org
            status = "created" if created else "already exists"
            self.stdout.write(f"  Organization '{org.name}' {status}")

        return orgs

    def _seed_superadmin(self):
        """Create the global superadmin user."""
        user, created = User.objects.get_or_create(
            username="superadmin",
            defaults={
                "email": "superadmin@intellidesk.in",
                "first_name": "Super",
                "last_name": "Admin",
                "organization": None,
                "role": User.Role.ADMIN,
                "is_superuser": True,
                "is_staff": True,
                "is_active": True,
            },
        )
        if created:
            user.set_password("Admin@123")
            user.save()
        status = "created" if created else "already exists"
        self.stdout.write(f"  Superadmin user {status}")

    def _seed_org_admins(self, orgs):
        """Create one admin per organization."""
        admin_data = [
            {
                "username": "colonyadmin",
                "org_key": "Green Valley Residency",
                "email": "colonyadmin@greenvalley.in",
                "first_name": "Rajesh",
                "last_name": "Sharma",
            },
            {
                "username": "sunriseadmin",
                "org_key": "Sunrise Colony",
                "email": "sunriseadmin@sunrise.in",
                "first_name": "Priya",
                "last_name": "Verma",
            },
            {
                "username": "techparkadmin",
                "org_key": "TechPark Business Center",
                "email": "techparkadmin@techpark.in",
                "first_name": "Arjun",
                "last_name": "Nair",
            },
        ]
        for data in admin_data:
            org = orgs[data["org_key"]]
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "organization": org,
                    "role": User.Role.ADMIN,
                    "is_staff": True,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("Admin@123")
                user.save()
            status = "created" if created else "already exists"
            self.stdout.write(f"  Admin '{data['username']}' {status}")

    def _seed_residents(self, orgs):
        """Create 4 residents per organization (12 total)."""
        gv = orgs["Green Valley Residency"]
        sun = orgs["Sunrise Colony"]
        tp = orgs["TechPark Business Center"]

        resident_data = [
            # Green Valley
            {"username": "gv_resident1", "org": gv, "email": "gv_resident1@greenvalley.in", "first_name": "Amit", "last_name": "Sharma"},
            {"username": "gv_resident2", "org": gv, "email": "gv_resident2@greenvalley.in", "first_name": "Neha", "last_name": "Gupta"},
            {"username": "gv_resident3", "org": gv, "email": "gv_resident3@greenvalley.in", "first_name": "Suresh", "last_name": "Kumar"},
            {"username": "gv_resident4", "org": gv, "email": "gv_resident4@greenvalley.in", "first_name": "Pooja", "last_name": "Singh"},
            # Sunrise Colony
            {"username": "sun_resident1", "org": sun, "email": "sun_resident1@sunrise.in", "first_name": "Rahul", "last_name": "Verma"},
            {"username": "sun_resident2", "org": sun, "email": "sun_resident2@sunrise.in", "first_name": "Kavita", "last_name": "Joshi"},
            {"username": "sun_resident3", "org": sun, "email": "sun_resident3@sunrise.in", "first_name": "Arun", "last_name": "Mishra"},
            {"username": "sun_resident4", "org": sun, "email": "sun_resident4@sunrise.in", "first_name": "Seema", "last_name": "Yadav"},
            # TechPark
            {"username": "tp_resident1", "org": tp, "email": "tp_resident1@techpark.in", "first_name": "Karan", "last_name": "Reddy"},
            {"username": "tp_resident2", "org": tp, "email": "tp_resident2@techpark.in", "first_name": "Meera", "last_name": "Nair"},
            {"username": "tp_resident3", "org": tp, "email": "tp_resident3@techpark.in", "first_name": "Sanjay", "last_name": "Pillai"},
            {"username": "tp_resident4", "org": tp, "email": "tp_resident4@techpark.in", "first_name": "Anita", "last_name": "Menon"},
        ]

        residents_by_org = {k: [] for k in orgs.keys()}
        for data in resident_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "organization": data["org"],
                    "role": User.Role.USER,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("User@123")
                user.save()
            status = "created" if created else "already exists"
            self.stdout.write(f"  Resident '{data['username']}' {status}")
            residents_by_org[data["org"].name].append(user)

        return residents_by_org

    def _seed_employee_users(self, orgs):
        """Create employee User accounts (15 total: 5 per org)."""
        gv = orgs["Green Valley Residency"]
        sun = orgs["Sunrise Colony"]
        tp = orgs["TechPark Business Center"]

        employee_data = [
            # Green Valley
            {"username": "gv_emp1", "org": gv, "first_name": "Ravi", "last_name": "Kumar", "email": "gv_emp1@greenvalley.in"},
            {"username": "gv_emp2", "org": gv, "first_name": "Sunil", "last_name": "Yadav", "email": "gv_emp2@greenvalley.in"},
            {"username": "gv_emp3", "org": gv, "first_name": "Mohan", "last_name": "Singh", "email": "gv_emp3@greenvalley.in"},
            {"username": "gv_emp4", "org": gv, "first_name": "Deepak", "last_name": "Patel", "email": "gv_emp4@greenvalley.in"},
            {"username": "gv_emp5", "org": gv, "first_name": "Anil", "last_name": "Gupta", "email": "gv_emp5@greenvalley.in"},
            # Sunrise Colony
            {"username": "sun_emp1", "org": sun, "first_name": "Vikram", "last_name": "Joshi", "email": "sun_emp1@sunrise.in"},
            {"username": "sun_emp2", "org": sun, "first_name": "Ramesh", "last_name": "Dubey", "email": "sun_emp2@sunrise.in"},
            {"username": "sun_emp3", "org": sun, "first_name": "Prakash", "last_name": "Tiwari", "email": "sun_emp3@sunrise.in"},
            {"username": "sun_emp4", "org": sun, "first_name": "Ajay", "last_name": "Mishra", "email": "sun_emp4@sunrise.in"},
            {"username": "sun_emp5", "org": sun, "first_name": "Nitin", "last_name": "Rawat", "email": "sun_emp5@sunrise.in"},
            # TechPark
            {"username": "tp_emp1", "org": tp, "first_name": "Suresh", "last_name": "Reddy", "email": "tp_emp1@techpark.in"},
            {"username": "tp_emp2", "org": tp, "first_name": "Kiran", "last_name": "Nair", "email": "tp_emp2@techpark.in"},
            {"username": "tp_emp3", "org": tp, "first_name": "Anand", "last_name": "Pillai", "email": "tp_emp3@techpark.in"},
            {"username": "tp_emp4", "org": tp, "first_name": "Manoj", "last_name": "Kumar", "email": "tp_emp4@techpark.in"},
            {"username": "tp_emp5", "org": tp, "first_name": "Rajiv", "last_name": "Menon", "email": "tp_emp5@techpark.in"},
        ]

        for data in employee_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "organization": data["org"],
                    "role": User.Role.EMPLOYEE,
                    "is_active": True,
                },
            )
            if created:
                user.set_password("Emp@123")
                user.save()
            status = "created" if created else "already exists"
            self.stdout.write(f"  Employee user '{data['username']}' {status}")

    # ─────────────────────────────────────────────────────────────────
    # Task 2.3 helper
    # ─────────────────────────────────────────────────────────────────

    def _seed_service_domains_and_issues(self, orgs):
        """Create 8 service domains and 5–6 predefined issues each, for all 3 orgs."""
        DOMAINS = [
            {"name": "Electrical",          "sla_hours": 4,  "icon_name": "Zap"},
            {"name": "Plumbing",            "sla_hours": 6,  "icon_name": "Droplets"},
            {"name": "HVAC / AC",           "sla_hours": 8,  "icon_name": "Wind"},
            {"name": "Cleaning",            "sla_hours": 24, "icon_name": "Sparkles"},
            {"name": "Carpentry",           "sla_hours": 48, "icon_name": "Hammer"},
            {"name": "Security",            "sla_hours": 2,  "icon_name": "Shield"},
            {"name": "IT Support",          "sla_hours": 8,  "icon_name": "Monitor"},
            {"name": "General Maintenance", "sla_hours": 24, "icon_name": "Wrench"},
        ]

        ISSUES = {
            "Electrical": [
                "Power socket not working",
                "Light fitting broken",
                "Circuit breaker tripping",
                "Electrical short circuit",
                "Switchboard damaged",
            ],
            "Plumbing": [
                "Pipe leakage",
                "Blocked drain",
                "No water supply",
                "Water heater not working",
                "Toilet flush issue",
            ],
            "HVAC / AC": [
                "AC not cooling",
                "AC making noise",
                "Thermostat not working",
                "AC water leakage",
                "Ventilation issue",
            ],
            "Cleaning": [
                "Common area cleaning",
                "Deep cleaning required",
                "Garbage disposal issue",
                "Pest control needed",
                "Window cleaning",
            ],
            "Carpentry": [
                "Door hinge broken",
                "Window frame damage",
                "Furniture repair needed",
                "Cabinet lock issue",
                "Flooring damage",
            ],
            "Security": [
                "CCTV camera not working",
                "Entry gate malfunction",
                "Suspicious activity report",
                "Access card issue",
                "Intercom not working",
            ],
            "IT Support": [
                "Internet not working",
                "WiFi signal weak",
                "IP Phone issue",
                "Printer not working",
                "Computer hardware fault",
            ],
            "General Maintenance": [
                "Wall paint peeling",
                "Roof leak",
                "Elevator issue",
                "Parking barrier broken",
                "Common area light out",
            ],
        }

        for org_name, org in orgs.items():
            for d_cfg in DOMAINS:
                domain, created = ServiceDomain.objects.get_or_create(
                    organization=org,
                    name=d_cfg["name"],
                    defaults={
                        "sla_hours": d_cfg["sla_hours"],
                        "icon_name": d_cfg["icon_name"],
                        "is_active": True,
                    },
                )
                status = "created" if created else "already exists"
                self.stdout.write(f"  Domain '{domain.name}' in '{org.name}' {status}")

                for title in ISSUES.get(d_cfg["name"], []):
                    issue, i_created = PredefinedIssue.objects.get_or_create(
                        domain=domain,
                        title=title,
                        defaults={
                            "default_priority": PredefinedIssue.Priority.NORMAL,
                            "is_active": True,
                        },
                    )
                    if i_created:
                        self.stdout.write(f"    Issue '{title}' created")

    # ─────────────────────────────────────────────────────────────────
    # Task 2.4 helper
    # ─────────────────────────────────────────────────────────────────

    def _seed_employee_profiles(self, orgs):
        """Create Employee records, skills, and Mon–Fri schedules."""
        gv  = orgs["Green Valley Residency"]
        sun = orgs["Sunrise Colony"]
        tp  = orgs["TechPark Business Center"]

        # (username, org, lat, lng, [(skill_domain_name, proficiency), ...], role_title)
        EMPLOYEE_CONFIGS = [
            # ── Green Valley ──────────────────────────────────────────────
            ("gv_emp1", gv, 28.6289, 77.3681, [("Electrical", 5), ("Plumbing", 3)],           "Technician"),
            ("gv_emp2", gv, 28.6251, 77.3645, [("Plumbing", 5), ("General Maintenance", 4)],  "Technician"),
            ("gv_emp3", gv, 28.6299, 77.3702, [("HVAC / AC", 5), ("Electrical", 3)],          "Senior Technician"),
            ("gv_emp4", gv, 28.6261, 77.3659, [("Cleaning", 5), ("Carpentry", 3)],            "Technician"),
            ("gv_emp5", gv, 28.6278, 77.3677, [("Security", 5), ("IT Support", 4)],           "Senior Technician"),
            # ── Sunrise Colony ────────────────────────────────────────────
            ("sun_emp1", sun, 28.7058, 77.1039, [("Electrical", 4), ("IT Support", 4)],           "Technician"),
            ("sun_emp2", sun, 28.7023, 77.1011, [("Plumbing", 5), ("Carpentry", 4)],             "Technician"),
            ("sun_emp3", sun, 28.7052, 77.1032, [("HVAC / AC", 4), ("General Maintenance", 5)],  "Senior Technician"),
            ("sun_emp4", sun, 28.7031, 77.1018, [("Cleaning", 5), ("Security", 3)],              "Technician"),
            ("sun_emp5", sun, 28.7047, 77.1028, [("Security", 5), ("Electrical", 3)],            "Senior Technician"),
            # ── TechPark ──────────────────────────────────────────────────
            ("tp_emp1", tp, 12.9368, 77.6262, [("IT Support", 5), ("Electrical", 4)],           "Senior Technician"),
            ("tp_emp2", tp, 12.9341, 77.6233, [("HVAC / AC", 5), ("General Maintenance", 3)],   "Technician"),
            ("tp_emp3", tp, 12.9359, 77.6251, [("Electrical", 4), ("Security", 5)],             "Senior Technician"),
            ("tp_emp4", tp, 12.9347, 77.6239, [("Plumbing", 4), ("Cleaning", 4)],              "Technician"),
            ("tp_emp5", tp, 12.9362, 77.6257, [("Carpentry", 5), ("General Maintenance", 4)],   "Technician"),
        ]

        for username, org, lat, lng, skills, role_title in EMPLOYEE_CONFIGS:
            # 1. Get the user account
            try:
                emp_user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  User '{username}' not found, skipping"))
                continue

            # 2. Get or create EmployeeRole for this org
            emp_role, _ = EmployeeRole.objects.get_or_create(
                organization=org,
                title=role_title,
                defaults={"description": f"{role_title} role"},
            )

            # 3. Get or create the Employee record
            employee, emp_created = Employee.objects.get_or_create(
                user=emp_user,
                defaults={
                    "organization": org,
                    "role": emp_role,
                    "experience_years": 3,
                    "max_active_assignments": 3,
                    "current_latitude": Decimal(str(lat)),
                    "current_longitude": Decimal(str(lng)),
                    "status": Employee.Status.ACTIVE,
                    "is_available": True,
                },
            )
            status = "created" if emp_created else "already exists"
            self.stdout.write(f"  Employee profile '{username}' {status}")

            # 4. Skills – update_or_create so proficiency can be updated on re-run
            for skill_name, proficiency in skills:
                try:
                    domain = ServiceDomain.objects.get(organization=org, name=skill_name)
                except ServiceDomain.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"    Domain '{skill_name}' not found in '{org.name}', skipping skill"
                    ))
                    continue

                EmployeeSkill.objects.update_or_create(
                    employee=employee,
                    domain=domain,
                    defaults={
                        "proficiency_level": proficiency,
                        "years_of_experience": proficiency,
                    },
                )
                self.stdout.write(f"    Skill '{skill_name}' (level {proficiency}) set for '{username}'")

            # 5. Mon–Fri schedules
            for day in range(5):  # 0=Mon … 4=Fri
                EmployeeSchedule.objects.get_or_create(
                    employee=employee,
                    day_of_week=day,
                    defaults={
                        "start_time": "09:00:00",
                        "end_time": "18:00:00",
                        "is_active": True,
                    },
                )

            self.stdout.write(f"    Schedules (Mon–Fri) ensured for '{username}'")

    # ─────────────────────────────────────────────────────────────────
    # Task 2.5 helper
    # ─────────────────────────────────────────────────────────────────

    def _seed_historical_requests(self, orgs, residents_by_org):
        """
        Seed:
          - 15 completed requests + Feedback (5 per org)
          - 5 active / in-progress requests
          - 3 urgent open requests
        """
        # Fixed baseline – keeps timestamps deterministic across runs
        baseline = datetime(2025, 1, 1, 9, 0, 0, tzinfo=dt_timezone.utc)

        # ── helpers ─────────────────────────────────────────────────
        def get_residents(org_name):
            return residents_by_org.get(org_name, [])

        def get_domains(org):
            return list(ServiceDomain.objects.filter(organization=org).order_by("name"))

        def get_issues(domain):
            return list(domain.predefined_issues.all().order_by("title"))

        def get_employees(org):
            return list(Employee.objects.filter(organization=org))

        # ── 15 completed requests (5 per org) ────────────────────────
        completed_idx = 0
        for org_name, org in orgs.items():
            residents = get_residents(org_name)
            domains   = get_domains(org)
            employees = get_employees(org)

            if not residents or not domains or not employees:
                self.stdout.write(self.style.WARNING(
                    f"  Skipping completed requests for '{org_name}' – missing residents/domains/employees"
                ))
                continue

            for i in range(5):
                resident = residents[i % len(residents)]
                domain   = domains[i % len(domains)]
                issues   = get_issues(domain)
                issue    = issues[i % len(issues)] if issues else None

                # Timestamps (past, deterministic)
                offset_days = completed_idx * 3 + 1
                created_at   = baseline - timedelta(days=offset_days + 30)
                sla_mult     = 0.8 + (completed_idx % 8) * 0.1   # 0.8 … 1.5×
                hours_taken  = domain.sla_hours * sla_mult
                completed_at = created_at + timedelta(hours=hours_taken)

                location_name = f"Completed-{org_name[:3].upper()}-{i + 1}"

                # Idempotent lookup
                req = ServiceRequest.objects.filter(
                    organization=org,
                    user=resident,
                    domain=domain,
                    location_name=location_name,
                ).first()

                if req is None:
                    req = ServiceRequest.objects.create(
                        organization=org,
                        user=resident,
                        domain=domain,
                        predefined_issue=issue,
                        location_name=location_name,
                        priority=ServiceRequest.Priority.NORMAL,
                        status=ServiceRequest.Status.CREATED,
                    )
                    # Bypass auto_now_add
                    ServiceRequest.objects.filter(pk=req.pk).update(
                        created_at=created_at,
                        completed_at=completed_at,
                        status=ServiceRequest.Status.COMPLETED,
                    )
                    req.refresh_from_db()
                    self.stdout.write(f"  Completed request '{location_name}' created")

                # Feedback – only if an Assignment exists for this request
                assignment = Assignment.objects.filter(request=req).first()
                if assignment and not hasattr(req, "feedback"):
                    try:
                        req.feedback  # check via related manager
                    except Feedback.DoesNotExist:
                        pass

                # Use get_or_create to stay idempotent
                fb_exists = Feedback.objects.filter(request=req).exists()
                if not fb_exists:
                    if assignment:
                        # Use the assigned employee for feedback
                        fb_employee = assignment.employee
                    else:
                        # Fall back to first available employee
                        fb_employee = employees[i % len(employees)]

                    is_resolved  = (completed_idx % 5) != 0  # 4 out of 5 resolved
                    rating       = random.randint(3, 5)
                    met_sla      = hours_taken <= domain.sla_hours
                    res_minutes  = int(timedelta(hours=hours_taken).total_seconds() / 60)

                    Feedback.objects.create(
                        request=req,
                        user=resident,
                        employee=fb_employee,
                        is_resolved=is_resolved,
                        rating=rating,
                        met_sla=met_sla,
                        resolution_time_minutes=res_minutes,
                        comments="Seeded demo feedback",
                    )
                    self.stdout.write(
                        f"    Feedback for '{location_name}' created "
                        f"(rating={rating}, met_sla={met_sla})"
                    )

                completed_idx += 1

        # ── 5 active / in-progress requests ──────────────────────────
        org_list      = list(orgs.values())
        org_name_list = list(orgs.keys())
        for i in range(5):
            org      = org_list[i % len(org_list)]
            org_name = org_name_list[i % len(org_name_list)]
            residents = get_residents(org_name)
            domains   = get_domains(org)

            if not residents or not domains:
                continue

            resident     = residents[i % len(residents)]
            domain       = domains[(i + 2) % len(domains)]
            issues       = get_issues(domain)
            issue        = issues[i % len(issues)] if issues else None
            location_name = f"Active-{i + 1}"
            status_choice = [
                ServiceRequest.Status.ASSIGNED,
                ServiceRequest.Status.IN_PROGRESS,
            ][i % 2]

            req = ServiceRequest.objects.filter(
                organization=org,
                user=resident,
                location_name=location_name,
            ).first()

            if req is None:
                req = ServiceRequest.objects.create(
                    organization=org,
                    user=resident,
                    domain=domain,
                    predefined_issue=issue,
                    location_name=location_name,
                    priority=ServiceRequest.Priority.NORMAL,
                    status=ServiceRequest.Status.CREATED,
                )
                ServiceRequest.objects.filter(pk=req.pk).update(
                    status=status_choice,
                )
                self.stdout.write(f"  Active request '{location_name}' created (status={status_choice})")

        # ── 3 urgent open requests ────────────────────────────────────
        for i in range(3):
            org      = org_list[i % len(org_list)]
            org_name = org_name_list[i % len(org_name_list)]
            residents = get_residents(org_name)
            domains   = get_domains(org)

            if not residents or not domains:
                continue

            resident      = residents[(i + 1) % len(residents)]
            domain        = domains[(i + 4) % len(domains)]
            issues        = get_issues(domain)
            issue         = issues[i % len(issues)] if issues else None
            location_name = f"Urgent-{i + 1}"

            req = ServiceRequest.objects.filter(
                organization=org,
                user=resident,
                location_name=location_name,
            ).first()

            if req is None:
                ServiceRequest.objects.create(
                    organization=org,
                    user=resident,
                    domain=domain,
                    predefined_issue=issue,
                    location_name=location_name,
                    priority=ServiceRequest.Priority.URGENT,
                    status=ServiceRequest.Status.CREATED,
                )
                self.stdout.write(f"  Urgent request '{location_name}' created")

    # ─────────────────────────────────────────────────────────────────
    # Summary counts
    # ─────────────────────────────────────────────────────────────────

    def _print_counts(self):
        from apps.requests.models import ServiceRequest as SR
        orgs_count     = Organization.objects.count()
        users_count    = User.objects.count()
        employees_count = Employee.objects.count()
        domains_count  = ServiceDomain.objects.count()
        issues_count   = PredefinedIssue.objects.count()
        requests_count = SR.objects.count()
        feedback_count = Feedback.objects.count()

        self.stdout.write(self.style.SUCCESS("\n── Final Record Counts ──────────────────"))
        self.stdout.write(f"  Organizations    : {orgs_count}")
        self.stdout.write(f"  Users            : {users_count}")
        self.stdout.write(f"  Employees        : {employees_count}")
        self.stdout.write(f"  Service Domains  : {domains_count}")
        self.stdout.write(f"  Predefined Issues: {issues_count}")
        self.stdout.write(f"  Service Requests : {requests_count}")
        self.stdout.write(f"  Feedback Records : {feedback_count}")
        self.stdout.write(self.style.SUCCESS("─────────────────────────────────────────\n"))

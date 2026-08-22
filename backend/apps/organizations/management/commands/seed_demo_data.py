from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.services.models import ServiceDomain, PredefinedIssue
from apps.employees.models import Employee, EmployeeRole, EmployeeSkill, EmployeeSchedule
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment
from apps.feedback.models import Feedback
from apps.ml_engine.distance import calculate_haversine_distance

class Command(BaseCommand):
    help = 'Seeds database with realistic multi-organization data, workforce, domains, and service requests'

    def handle(self, *args, **options):
        self.stdout.write('Seeding demo data...')

        # 1. Create Superuser / Global Admin
        if not User.objects.filter(username='superadmin').exists():
            User.objects.create_superuser('superadmin', 'superadmin@platform.io', 'password123')
            self.stdout.write('Created superuser: superadmin / password123')

        # 2. Create Organizations
        org_data = [
            {
                'name': 'Greenwood Residential Colony',
                'org_type': Organization.OrgType.RESIDENTIAL_COLONY,
                'address': 'Outer Ring Road, Bellandur, Bengaluru',
                'latitude': 12.9304,
                'longitude': 77.6784,
                'contact_email': 'mgmt@greenwoodcolony.org',
                'contact_phone': '+91 98800 12345',
            },
            {
                'name': 'Silver Oaks Gated Community',
                'org_type': Organization.OrgType.GATED_COMMUNITY,
                'address': 'Koramangala 4th Block, Bengaluru',
                'latitude': 12.9352,
                'longitude': 77.6245,
                'contact_email': 'contact@silveroaks.org',
                'contact_phone': '+91 98800 23456',
            },
            {
                'name': 'CyberPulse Tech Park & Offices',
                'org_type': Organization.OrgType.OFFICE_SPACE,
                'address': 'Whitefield Main Road, Bengaluru',
                'latitude': 12.9850,
                'longitude': 77.7300,
                'contact_email': 'facilities@cyberpulse.com',
                'contact_phone': '+91 98800 34567',
            }
        ]

        orgs = {}
        for od in org_data:
            org, _ = Organization.objects.get_or_create(name=od['name'], defaults=od)
            orgs[od['name']] = org

        primary_org = orgs['Greenwood Residential Colony']

        # 3. Create Admin Users
        admins = [
            ('admin_greenwood', 'admin_gw@greenwoodcolony.org', primary_org, 'Greenwood', 'Administrator'),
            ('admin_silveroaks', 'admin_so@silveroaks.org', orgs['Silver Oaks Gated Community'], 'SilverOaks', 'Administrator'),
            ('admin_cyberpulse', 'admin_cp@cyberpulse.com', orgs['CyberPulse Tech Park & Offices'], 'CyberPulse', 'Administrator'),
        ]
        for uname, email, org, fn, ln in admins:
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(
                    username=uname,
                    email=email,
                    password='password123',
                    organization=org,
                    role=User.Role.ADMIN,
                    first_name=fn,
                    last_name=ln
                )

        # 4. Create Service Domains and Predefined Issues for Greenwood
        domain_definitions = [
            {
                'name': 'Electrical',
                'sla_hours': 8,
                'description': 'Power supply, wiring, switchboards, lighting, circuit breakers, and backup generator support.',
                'icon_name': 'Zap',
                'issues': [
                    ('Power Outage in Unit', 'URGENT', 45),
                    ('Flickering Lights / Low Voltage', 'NORMAL', 30),
                    ('Switch / Socket Sparking', 'HIGH', 30),
                    ('Circuit Breaker Tripping Constantly', 'URGENT', 60),
                    ('Ceiling Fan / Fixture Repair', 'LOW', 45),
                ]
            },
            {
                'name': 'Plumbing',
                'sla_hours': 6,
                'description': 'Pipes, faucets, drain blockage, sanitary fittings, water tank and geyser installations.',
                'icon_name': 'Droplets',
                'issues': [
                    ('Major Water Pipeline Burst', 'CRITICAL', 30),
                    ('Severe Drain Blockage / Overflow', 'HIGH', 45),
                    ('Low Water Pressure in Taps', 'NORMAL', 30),
                    ('Leaking Faucet / Fixture', 'LOW', 30),
                    ('Geyser / Water Heater Not Working', 'NORMAL', 60),
                ]
            },
            {
                'name': 'HVAC & Air Conditioning',
                'sla_hours': 12,
                'description': 'Central cooling, split AC units, ventilation ducts, compressors, and heating elements.',
                'icon_name': 'Fan',
                'issues': [
                    ('AC Not Cooling at All', 'HIGH', 60),
                    ('Water Dripping from Indoor AC Unit', 'NORMAL', 45),
                    ('Loud Compressor Noise / Vibration', 'NORMAL', 60),
                    ('Seasonal Duct & Filter Cleaning', 'LOW', 90),
                ]
            },
            {
                'name': 'Carpentry & Civil',
                'sla_hours': 24,
                'description': 'Doors, windows, modular fittings, lock repair, ceiling seepage, and civil masonry.',
                'icon_name': 'Hammer',
                'issues': [
                    ('Main Door Digital Lock Malfunction', 'HIGH', 45),
                    ('Broken Window Glass / Latch', 'NORMAL', 60),
                    ('Balcony Door Jammed', 'NORMAL', 45),
                    ('Wall Crack / Water Seepage Inspection', 'LOW', 120),
                ]
            },
            {
                'name': 'Cleaning & Waste Management',
                'sla_hours': 24,
                'description': 'Housekeeping, deep sanitization, trash clearance, common area maintenance.',
                'icon_name': 'Sparkles',
                'issues': [
                    ('Immediate Spill & Sanitization', 'HIGH', 30),
                    ('Bulk Waste & Debris Disposal', 'LOW', 60),
                    ('Common Corridor Deep Clean', 'NORMAL', 90),
                ]
            },
            {
                'name': 'Security & Surveillance',
                'sla_hours': 4,
                'description': 'CCTV cameras, smart access cards, perimeter sensors, boom barriers, intercom systems.',
                'icon_name': 'Shield',
                'issues': [
                    ('Boom Barrier Gate Stuck', 'URGENT', 20),
                    ('Intercom Not Connecting to Gate', 'NORMAL', 30),
                    ('CCTV Blind Spot / Camera Offline', 'HIGH', 45),
                    ('Resident Access Card Demagnetized', 'LOW', 15),
                ]
            },
            {
                'name': 'IT & Network Infrastructure',
                'sla_hours': 4,
                'description': 'Fiber optic line, Wi-Fi access points, clubhouse network, community portal kiosks.',
                'icon_name': 'Wifi',
                'issues': [
                    ('Fiber Internet Disconnected', 'URGENT', 45),
                    ('Wi-Fi Router Reset Required', 'NORMAL', 30),
                    ('Clubhouse Video Screen Network Issue', 'LOW', 60),
                ]
            },
            {
                'name': 'General Maintenance',
                'sla_hours': 36,
                'description': 'Pest control, lift maintenance escort, garden sprinkler fixes, miscellaneous handyman tasks.',
                'icon_name': 'Wrench',
                'issues': [
                    ('Lift Floor Indicator Glitch', 'HIGH', 45),
                    ('Sprinkler Line Broken in Lawn', 'NORMAL', 60),
                    ('Pest Infestation Treatment Request', 'NORMAL', 90),
                ]
            },
        ]

        created_domains = {}
        for ddef in domain_definitions:
            dom, _ = ServiceDomain.objects.get_or_create(
                organization=primary_org,
                name=ddef['name'],
                defaults={
                    'sla_hours': ddef['sla_hours'],
                    'description': ddef['description'],
                    'icon_name': ddef['icon_name'],
                }
            )
            created_domains[ddef['name']] = dom
            for ititle, ipriority, idur in ddef['issues']:
                PredefinedIssue.objects.get_or_create(
                    domain=dom,
                    title=ititle,
                    defaults={
                        'default_priority': ipriority,
                        'estimated_duration_minutes': idur
                    }
                )

        # 5. Create Employee Roles
        roles_data = [
            ('Senior Lead Technician', 'Expert in multi-trade troubleshooting and mission-critical interventions.'),
            ('Licensed Electrician', 'Certified electrical specialist for residential & commercial installations.'),
            ('Master Plumber', 'Sanitary engineering, high-pressure line specialist, water management.'),
            ('HVAC Engineer', 'Air conditioning, cooling loops, thermal controls.'),
            ('Network & Security Specialist', 'Smart infrastructure, IoT access control, fiber networks.'),
            ('Facility Maintenance Associate', 'General repairs, civil fixtures, housekeeping supervision.'),
        ]
        created_roles = {}
        for rtitle, rdesc in roles_data:
            role_obj, _ = EmployeeRole.objects.get_or_create(
                organization=primary_org,
                title=rtitle,
                defaults={'description': rdesc}
            )
            created_roles[rtitle] = role_obj

        # 6. Create Employees with Varied Locations, Skills, and Schedules
        # Coordinates around Greenwood Colony (12.9304, 77.6784)
        employees_spec = [
            {
                'username': 'emp_rajesh',
                'first_name': 'Rajesh',
                'last_name': 'Sharma',
                'email': 'rajesh.sharma@workforce.io',
                'phone': '+91 98765 11001',
                'role': created_roles['Licensed Electrician'],
                'experience': 7,
                'max_active': 3,
                'lat': 12.9312,
                'lng': 77.6790, # ~0.1 km away
                'skills': [('Electrical', 5, 7), ('HVAC & Air Conditioning', 3, 3)],
            },
            {
                'username': 'emp_vikram',
                'first_name': 'Vikram',
                'last_name': 'Patel',
                'email': 'vikram.patel@workforce.io',
                'phone': '+91 98765 11002',
                'role': created_roles['Licensed Electrician'],
                'experience': 3,
                'max_active': 3,
                'lat': 12.9450,
                'lng': 77.6920, # ~2.2 km away
                'skills': [('Electrical', 3, 3), ('General Maintenance', 4, 3)],
            },
            {
                'username': 'emp_suresh',
                'first_name': 'Suresh',
                'last_name': 'Kumar',
                'email': 'suresh.kumar@workforce.io',
                'phone': '+91 98765 11003',
                'role': created_roles['Master Plumber'],
                'experience': 10,
                'max_active': 4,
                'lat': 12.9298,
                'lng': 77.6775, # ~0.15 km away
                'skills': [('Plumbing', 5, 10), ('General Maintenance', 4, 5)],
            },
            {
                'username': 'emp_amit',
                'first_name': 'Amit',
                'last_name': 'Verma',
                'email': 'amit.verma@workforce.io',
                'phone': '+91 98765 11004',
                'role': created_roles['Master Plumber'],
                'experience': 4,
                'max_active': 3,
                'lat': 12.9520,
                'lng': 77.6610, # ~3.1 km away
                'skills': [('Plumbing', 3, 4), ('Carpentry & Civil', 3, 3)],
            },
            {
                'username': 'emp_rohan',
                'first_name': 'Rohan',
                'last_name': 'Mehta',
                'email': 'rohan.mehta@workforce.io',
                'phone': '+91 98765 11005',
                'role': created_roles['HVAC Engineer'],
                'experience': 6,
                'max_active': 3,
                'lat': 12.9320,
                'lng': 77.6810, # ~0.3 km away
                'skills': [('HVAC & Air Conditioning', 5, 6), ('Electrical', 4, 5)],
            },
            {
                'username': 'emp_anil',
                'first_name': 'Anil',
                'last_name': 'Kapoor',
                'email': 'anil.kapoor@workforce.io',
                'phone': '+91 98765 11006',
                'role': created_roles['Network & Security Specialist'],
                'experience': 5,
                'max_active': 4,
                'lat': 12.9300,
                'lng': 77.6780, # ~0.05 km away
                'skills': [('IT & Network Infrastructure', 5, 5), ('Security & Surveillance', 5, 5)],
            },
            {
                'username': 'emp_deepak',
                'first_name': 'Deepak',
                'last_name': 'Joshi',
                'email': 'deepak.joshi@workforce.io',
                'phone': '+91 98765 11007',
                'role': created_roles['Senior Lead Technician'],
                'experience': 8,
                'max_active': 3,
                'lat': 12.9310,
                'lng': 77.6770, # ~0.18 km away
                'skills': [('Carpentry & Civil', 5, 8), ('Cleaning & Waste Management', 4, 6), ('General Maintenance', 5, 8)],
            },
        ]

        created_employees = []
        for espec in employees_spec:
            user, _ = User.objects.get_or_create(
                username=espec['username'],
                defaults={
                    'email': espec['email'],
                    'first_name': espec['first_name'],
                    'last_name': espec['last_name'],
                    'phone': espec['phone'],
                    'role': User.Role.EMPLOYEE,
                    'organization': primary_org,
                }
            )
            user.set_password('password123')
            user.save()

            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'organization': primary_org,
                    'role': espec['role'],
                    'experience_years': espec['experience'],
                    'max_active_assignments': espec['max_active'],
                    'current_latitude': espec['lat'],
                    'current_longitude': espec['lng'],
                    'status': Employee.Status.ACTIVE,
                    'is_available': True,
                }
            )
            created_employees.append(emp)

            # Assign skills
            for dom_name, prof_lvl, yrs_exp in espec['skills']:
                if dom_name in created_domains:
                    EmployeeSkill.objects.get_or_create(
                        employee=emp,
                        domain=created_domains[dom_name],
                        defaults={
                            'proficiency_level': prof_lvl,
                            'years_of_experience': yrs_exp,
                        }
                    )

            # Create default 7-day schedule
            for day in range(7):
                EmployeeSchedule.objects.get_or_create(
                    employee=emp,
                    day_of_week=day,
                    defaults={
                        'start_time': '08:00:00',
                        'end_time': '20:00:00',
                        'is_active': True,
                    }
                )

        # 7. Create Resident Users
        residents_spec = [
            ('resident_neha', 'Neha', 'Sharma', 'neha.sharma@example.com', 'Tower A, Apt 402', 12.9304, 77.6784),
            ('resident_karan', 'Karan', 'Singhania', 'karan.s@example.com', 'Villa 18, Palm Avenue', 12.9308, 77.6789),
            ('resident_priya', 'Priya', 'Nair', 'priya.nair@example.com', 'Tower B, Apt 1104', 12.9302, 77.6780),
            ('resident_rahul', 'Rahul', 'Deshmukh', 'rahul.d@example.com', 'Tower C, Apt 701', 12.9305, 77.6786),
        ]
        created_residents = []
        for uname, fn, ln, email, addr, rlat, rlng in residents_spec:
            res_user, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    'first_name': fn,
                    'last_name': ln,
                    'email': email,
                    'phone': '+91 99000 88776',
                    'role': User.Role.USER,
                    'organization': primary_org,
                    'address': addr,
                }
            )
            res_user.set_password('password123')
            res_user.save()
            created_residents.append((res_user, addr, rlat, rlng))

        # 8. Create Realistic Historical Requests, Assignments & Feedbacks
        self.stdout.write('Seeding historical requests & resolution logs...')
        now = timezone.now()

        historical_samples = [
            # Electrical requests
            (created_domains['Electrical'], 'Switch / Socket Sparking', 'Kitchen microwave socket threw sparks when plugged in.', 'HIGH', 10, True, 5, 'Rajesh arrived within 15 minutes, replaced the damaged wall socket safely. Very professional!'),
            (created_domains['Electrical'], 'Flickering Lights / Low Voltage', 'Living room ceiling lights flickering continuously since yesterday.', 'NORMAL', 8, True, 5, 'Quick fix on the main distribution box connection.'),
            (created_domains['Electrical'], 'Circuit Breaker Tripping Constantly', 'Master bedroom MCB trips as soon as geyser is turned on.', 'URGENT', 6, True, 4, 'Identified neutral leakage in geyser element and fixed it.'),
            
            # Plumbing requests
            (created_domains['Plumbing'], 'Major Water Pipeline Burst', 'Under-sink pipe joint ruptured, water flooding the utility area!', 'CRITICAL', 12, True, 5, 'Suresh arrived immediately and isolated the valve in under 10 minutes. Lifesaver!'),
            (created_domains['Plumbing'], 'Severe Drain Blockage / Overflow', 'Balcony drain is completely choked during heavy rain.', 'HIGH', 9, True, 4, 'Cleared deep debris from drain outlet.'),
            (created_domains['Plumbing'], 'Leaking Faucet / Fixture', 'Bathroom basin tap has a constant slow drip.', 'LOW', 5, True, 5, 'Replaced the ceramic cartridge cleanly.'),

            # HVAC requests
            (created_domains['HVAC & Air Conditioning'], 'AC Not Cooling at All', 'Master bedroom split AC running but blowing room temperature air.', 'HIGH', 7, True, 5, 'Rohan checked refrigerant pressure and refilled gas. Cooling works great now.'),
            (created_domains['HVAC & Air Conditioning'], 'Water Dripping from Indoor AC Unit', 'AC indoor unit condensate tray is overflowing onto the wooden floor.', 'NORMAL', 4, True, 4, 'Unclogged the drain line.'),

            # Security requests
            (created_domains['Security & Surveillance'], 'Boom Barrier Gate Stuck', 'Visitor entrance boom barrier not opening on RFID scan.', 'URGENT', 3, True, 5, 'Anil reset the controller board and recalibrated optical sensor.'),
            (created_domains['Security & Surveillance'], 'Intercom Not Connecting to Gate', 'Apartment intercom phone has no dial tone to main security guardhouse.', 'NORMAL', 2, True, 4, 'Replaced faulty RJ11 connector wire.'),

            # IT requests
            (created_domains['IT & Network Infrastructure'], 'Fiber Internet Disconnected', 'Optical fiber signal indicator blinking red on community gateway.', 'URGENT', 2, True, 5, 'Spliced damaged fiber patch lead swiftly.'),

            # Carpentry & Civil requests
            (created_domains['Carpentry & Civil'], 'Main Door Digital Lock Malfunction', 'Smart keypad lock gives error beep and does not accept passcode.', 'HIGH', 1, True, 5, 'Deepak replaced lock motor unit and reprogrammed access.'),
        ]

        for dom, issue_title, custom_desc, prio, days_ago, is_res, rating_val, comment_text in historical_samples:
            res_user, addr, rlat, rlng = random.choice(created_residents)
            issue_obj = dom.predefined_issues.filter(title=issue_title).first()
            created_dt = now - timedelta(days=days_ago, hours=random.randint(1, 8))
            in_prog_dt = created_dt + timedelta(minutes=random.randint(15, 45))
            comp_dt = in_prog_dt + timedelta(minutes=random.randint(30, 90))

            req = ServiceRequest.objects.create(
                organization=primary_org,
                user=res_user,
                domain=dom,
                predefined_issue=issue_obj,
                custom_description=custom_desc,
                latitude=rlat,
                longitude=rlng,
                location_name=addr,
                priority=prio,
                status=ServiceRequest.Status.COMPLETED,
                created_at=created_dt,
                in_progress_at=in_prog_dt,
                completed_at=comp_dt,
            )
            # Find an employee matching domain
            matching_emp = Employee.objects.filter(organization=primary_org, skills__domain=dom).first() or created_employees[0]
            dist = calculate_haversine_distance(rlat, rlng, float(matching_emp.current_latitude), float(matching_emp.current_longitude))

            assignment = Assignment.objects.create(
                request=req,
                employee=matching_emp,
                status=Assignment.Status.COMPLETED,
                request_latitude_snapshot=rlat,
                request_longitude_snapshot=rlng,
                employee_latitude_snapshot=matching_emp.current_latitude,
                employee_longitude_snapshot=matching_emp.current_longitude,
                distance_km=dist,
                active_workload_at_assignment=0,
                features_snapshot={
                    'distance_km': dist,
                    'domain_proficiency': 5,
                    'experience_years': matching_emp.experience_years,
                    'historical_avg_rating': 5.0,
                    'historical_success_rate': 1.0,
                },
                suitability_score=0.92,
                ranking_model_version='placeholder-deterministic-v1',
                assigned_at=created_dt,
                accepted_at=in_prog_dt,
                completed_at=comp_dt,
            )

            res_mins = int((comp_dt - created_dt).total_seconds() / 60)
            Feedback.objects.create(
                request=req,
                user=res_user,
                employee=matching_emp,
                is_resolved=is_res,
                rating=rating_val,
                comments=comment_text,
                resolution_time_minutes=res_mins,
                met_sla=True,
                created_at=comp_dt + timedelta(minutes=15)
            )

        # 9. Create Active / Live Requests to test dashboards right away
        live_samples = [
            (created_domains['Electrical'], 'Power Outage in Unit', 'Main circuit tripped during heavy load. No power in kitchen and hall.', 'URGENT', ServiceRequest.Status.IN_PROGRESS),
            (created_domains['Plumbing'], 'Severe Drain Blockage / Overflow', 'Kitchen sink draining extremely slowly and gurgling back up.', 'HIGH', ServiceRequest.Status.ASSIGNED),
            (created_domains['HVAC & Air Conditioning'], 'Loud Compressor Noise / Vibration', 'Split AC makes metallic rattling noise when turned on.', 'NORMAL', ServiceRequest.Status.ASSIGNED),
            (created_domains['Carpentry & Civil'], 'Balcony Door Jammed', 'Sliding glass door track jammed, difficult to open.', 'LOW', ServiceRequest.Status.QUEUED),
        ]

        for dom, issue_title, custom_desc, prio, req_status in live_samples:
            res_user, addr, rlat, rlng = random.choice(created_residents)
            issue_obj = dom.predefined_issues.filter(title=issue_title).first()

            req = ServiceRequest.objects.create(
                organization=primary_org,
                user=res_user,
                domain=dom,
                predefined_issue=issue_obj,
                custom_description=custom_desc,
                latitude=rlat,
                longitude=rlng,
                location_name=addr,
                priority=prio,
                status=req_status,
                in_progress_at=now - timedelta(minutes=30) if req_status == ServiceRequest.Status.IN_PROGRESS else None,
            )

            if req_status in [ServiceRequest.Status.ASSIGNED, ServiceRequest.Status.IN_PROGRESS]:
                matching_emp = Employee.objects.filter(organization=primary_org, skills__domain=dom).first() or created_employees[0]
                dist = calculate_haversine_distance(rlat, rlng, float(matching_emp.current_latitude), float(matching_emp.current_longitude))

                Assignment.objects.create(
                    request=req,
                    employee=matching_emp,
                    status=Assignment.Status.IN_PROGRESS if req_status == ServiceRequest.Status.IN_PROGRESS else Assignment.Status.ASSIGNED,
                    request_latitude_snapshot=rlat,
                    request_longitude_snapshot=rlng,
                    employee_latitude_snapshot=matching_emp.current_latitude,
                    employee_longitude_snapshot=matching_emp.current_longitude,
                    distance_km=dist,
                    active_workload_at_assignment=1,
                    features_snapshot={
                        'distance_km': dist,
                        'domain_proficiency': 4,
                        'experience_years': matching_emp.experience_years,
                        'historical_avg_rating': 4.9,
                    },
                    suitability_score=0.88,
                    ranking_model_version='placeholder-deterministic-v1',
                    assigned_at=now - timedelta(minutes=45),
                    accepted_at=now - timedelta(minutes=30) if req_status == ServiceRequest.Status.IN_PROGRESS else None,
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded complete demo dataset!'))
        self.stdout.write(self.style.SUCCESS('Demo Accounts Available:'))
        self.stdout.write('  Super Admin: superadmin / password123')
        self.stdout.write('  Colony Admin: admin_greenwood / password123')
        self.stdout.write('  Electrician: emp_rajesh / password123')
        self.stdout.write('  Plumber: emp_suresh / password123')
        self.stdout.write('  Resident: resident_neha / password123')

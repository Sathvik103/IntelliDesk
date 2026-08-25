"""
Idempotent management command to ensure development/demo users exist
with predictable credentials.

Accounts created (or updated if they already exist):

  superadmin   / Admin@123    (ADMIN, is_superuser, no org)
  colonyadmin  / Admin@123    (ADMIN, Green Valley Residency)
  resident1    / User@123     (USER,  Green Valley Residency)
  electrician1 / Employee@123 (EMPLOYEE, Green Valley Residency)
  plumber1     / Employee@123 (EMPLOYEE, Green Valley Residency)

Run with:
    python manage.py ensure_dev_users
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = "Ensure required development/demo accounts exist with correct passwords (idempotent)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n=== Ensuring development users ===\n"))

        # Get or create a primary organization for dev users
        org, org_created = Organization.objects.get_or_create(
            name="Green Valley Residency",
            defaults={
                "org_type": "GATED_COMMUNITY",
                "address": "Sector 62, Noida, UP",
                "contact_email": "admin@greenvalley.in",
                "contact_phone": "+91-120-4567890",
                "is_active": True,
            },
        )
        self.stdout.write(f"  Organization 'Green Valley Residency' {'created' if org_created else 'exists'}")

        accounts = [
            {
                "username": "superadmin",
                "password": "Admin@123",
                "email": "superadmin@intellidesk.in",
                "first_name": "Super",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "organization": None,
                "is_superuser": True,
                "is_staff": True,
                "is_active": True,
            },
            {
                "username": "colonyadmin",
                "password": "Admin@123",
                "email": "colonyadmin@greenvalley.in",
                "first_name": "Rajesh",
                "last_name": "Sharma",
                "role": User.Role.ADMIN,
                "organization": org,
                "is_superuser": False,
                "is_staff": True,
                "is_active": True,
            },
            {
                "username": "resident1",
                "password": "User@123",
                "email": "resident1@greenvalley.in",
                "first_name": "Amit",
                "last_name": "Sharma",
                "role": User.Role.USER,
                "organization": org,
                "is_superuser": False,
                "is_staff": False,
                "is_active": True,
            },
            {
                "username": "electrician1",
                "password": "Employee@123",
                "email": "electrician1@greenvalley.in",
                "first_name": "Ravi",
                "last_name": "Kumar",
                "role": User.Role.EMPLOYEE,
                "organization": org,
                "is_superuser": False,
                "is_staff": False,
                "is_active": True,
            },
            {
                "username": "plumber1",
                "password": "Employee@123",
                "email": "plumber1@greenvalley.in",
                "first_name": "Suresh",
                "last_name": "Patel",
                "role": User.Role.EMPLOYEE,
                "organization": org,
                "is_superuser": False,
                "is_staff": False,
                "is_active": True,
            },
        ]

        for account in accounts:
            password = account.pop("password")
            username = account["username"]

            user, created = User.objects.get_or_create(
                username=username,
                defaults=account,
            )

            # Always set the password to ensure it matches, whether created or existing
            user.set_password(password)
            # Ensure role/status is correct on existing users too
            user.role = account["role"]
            user.is_active = account["is_active"]
            user.is_superuser = account["is_superuser"]
            user.is_staff = account["is_staff"]
            if account.get("organization") is not None:
                user.organization = account["organization"]
            user.save()

            action = "created" if created else "updated password"
            self.stdout.write(f"  [{account['role']}] {username} — {action}")

        self.stdout.write(self.style.SUCCESS("\n=== Development users ready ===\n"))
        self.stdout.write("Credentials:")
        self.stdout.write("  superadmin   / Admin@123")
        self.stdout.write("  colonyadmin  / Admin@123")
        self.stdout.write("  resident1    / User@123")
        self.stdout.write("  electrician1 / Employee@123")
        self.stdout.write("  plumber1     / Employee@123")
        self.stdout.write("")

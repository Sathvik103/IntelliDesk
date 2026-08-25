import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.accounts.models import User
print("=== Seeded Users ===")
users = User.objects.values('username', 'role', 'is_active', 'is_superuser').order_by('role', 'username')
for u in users:
    print("  %-22s role=%-10s active=%-5s super=%s" % (u['username'], u['role'], u['is_active'], u['is_superuser']))
print("Total:", users.count())

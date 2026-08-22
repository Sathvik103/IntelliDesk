# Technical Design — IntelliDesk Phase 3

## Overview

IntelliDesk Phase 3 is a complete production-ready build of an intelligent workforce helpdesk SaaS platform. This document specifies the technical architecture, implementation structure, and component interactions necessary to satisfy the 14 requirements established in `requirements.md`.

The system spans a Django/PostgreSQL REST backend, a Next.js frontend, and a pre-trained Keras ML ranking model. The design preserves existing backend architecture (CandidateSelector, FeatureBuilder, RankingModelInterface, AssignmentService) and focuses on: (1) fixing the authentication initialization bug, (2) establishing idempotent seed data, (3) redesigning all three user portals, (4) introducing a limited Super Admin dashboard, and (5) implementing a dynamic multi-step request wizard.

---

## Architecture Overview

### Backend (Django/PostgreSQL)

```
Backend Directory Structure:
├── config/
│   ├── settings.py          (JWT + CORS already configured)
│   └── urls.py              (API routes)
├── apps/
│   ├── accounts/
│   │   ├── views.py         (LoginView, RegisterView, CurrentUserView, UserViewSet)
│   │   ├── serializers.py   (UserSerializer, LoginSerializer, RegisterSerializer)
│   │   ├── models.py        (User model with role/organization/phone/address)
│   │   ├── urls.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── seed_demo_data.py  (NEW: Idempotent seed command)
│   │   ├── permissions.py   (IsAdminRole, IsEmployeeRole)
│   │   ├── tests.py         (Authentication, Authorization, Isolation tests)
│   │   └── migrations/
│   ├── organizations/
│   │   ├── models.py        (Organization with OrgType, address, lat/lng, contact_phone)
│   │   ├── views.py         (OrganizationViewSet with activate/deactivate/org_types)
│   │   └── tests.py         (Organization isolation tests)
│   ├── services/
│   │   ├── models.py        (ServiceDomain, PredefinedIssue)
│   │   ├── views.py         (ServiceDomainViewSet, PredefinedIssueViewSet)
│   │   ├── serializers.py
│   │   └── tests.py         (ServiceDomain CRUD tests)
│   ├── employees/
│   │   ├── models.py        (Employee, EmployeeRole, EmployeeSkill, EmployeeSchedule)
│   │   ├── views.py         (EmployeeViewSet with me/update_location/set_status actions)
│   │   ├── serializers.py
│   │   └── tests.py         (Employee CRUD, skill, schedule tests)
│   ├── requests/
│   │   ├── models.py        (ServiceRequest + NEW: details_snapshot JSONField)
│   │   ├── views.py         (ServiceRequestViewSet with status transitions)
│   │   ├── serializers.py   (ServiceRequestSerializer)
│   │   ├── urls.py
│   │   └── tests.py         (Request creation, status transitions, assignment tests)
│   ├── assignments/
│   │   ├── models.py        (Assignment with snapshots)
│   │   ├── views.py         (AssignmentViewSet with accept/reassign)
│   │   ├── serializers.py
│   │   └── migrations/
│   ├── feedback/
│   │   ├── models.py        (Feedback with is_resolved/rating/resolution_time/met_sla)
│   │   ├── views.py         (FeedbackViewSet)
│   │   ├── serializers.py
│   │   └── tests.py         (Feedback submit, reopen on unresolved tests)
│   ├── analytics/
│   │   ├── views.py         (AnalyticsOverviewView + NEW: PlatformAnalyticsView)
│   │   ├── services.py      (AnalyticsService with fixed N+1 query)
│   │   └── tests.py
│   └── ml_engine/
│       ├── interfaces.py     (RankingModelInterface)
│       ├── selector.py       (CandidateSelector)
│       ├── feature_builder.py
│       ├── placeholder_ranker.py (DeterministicWeightedRanker — active)
│       ├── keras_ranker.py   (KerasRankingModel — NOT USED in production)
│       ├── service.py        (AssignmentService — UNCHANGED)
│       ├── helpdesk_assignment_model.keras (Keras model file)
│       ├── helpdesk_preprocessor.pkl
│       └── tests.py          (Distance, selector, feature builder, ranker tests)
├── requirements.txt
└── manage.py
```

### Frontend (Next.js + React)

```
Frontend Directory Structure:
├── app/
│   ├── layout.tsx           (Root layout with AuthProvider)
│   ├── page.tsx             (Home → HelpdeskApp)
│   └── globals.css          (NEW: Design system — Inter font, color palette, CSS variables)
├── components/
│   └── helpdesk/
│       ├── HelpdeskApp.tsx           (Main router component — role-based portal selection)
│       ├── Navbar.tsx                (FIXED: Remove role switcher, fix ZapIcon import)
│       ├── AuthModal.tsx             (FIXED: Remove role selector from register form)
│       ├── portals/
│       │   ├── SuperAdminPortal.tsx  (NEW: Platform KPIs, orgs, users)
│       │   ├── AdminPortal.tsx       (REDESIGN: Sidebar nav, dashboard, requests, workforce, services, users)
│       │   ├── EmployeePortal.tsx    (REDESIGN: Sidebar nav, active tasks, history, profile)
│       │   └── ResidentPortal.tsx    (REDESIGN: Request cards, new request button)
│       ├── wizard/
│       │   ├── RequestWizard.tsx     (NEW: 6-step form wizard)
│       │   ├── WizardStep.tsx        (NEW: Base wizard step component)
│       │   ├── steps/
│       │   │   ├── ServiceStep.tsx          (Step 1: Domain selection)
│       │   │   ├── ProblemStep.tsx          (Step 2: Predefined issue)
│       │   │   ├── DetailsStep.tsx          (Step 3: Domain-specific fields)
│       │   │   ├── LocationStep.tsx         (Step 4: Org-type-specific location)
│       │   │   ├── PriorityStep.tsx         (Step 5: Priority selector)
│       │   │   └── ReviewStep.tsx           (Step 6: Final review)
│       │   └── domainForms/
│       │       ├── ElectricalForm.tsx       (Electrical-specific fields)
│       │       ├── PlumbingForm.tsx
│       │       ├── HVACForm.tsx
│       │       ├── CleaningForm.tsx
│       │       ├── CarpentryForm.tsx
│       │       ├── SecurityForm.tsx
│       │       ├── ITSupportForm.tsx
│       │       └── GeneralMaintenanceForm.tsx
│       ├── shared/
│       │   ├── Sidebar.tsx            (NEW: Admin/Employee sidebar navigation)
│       │   ├── KPICard.tsx            (NEW: Reusable KPI card component)
│       │   ├── RequestCard.tsx        (NEW: Request card with domain colors)
│       │   ├── AssignmentCard.tsx     (NEW: Assignment card for employee)
│       │   ├── SkeletonLoader.tsx     (NEW: Loading state component)
│       │   └── EmptyState.tsx         (NEW: Empty state illustration)
│       ├── modals/
│       │   ├── FeedbackModal.tsx      (EXISTING: Feedback form modal)
│       │   └── CandidateInspectorModal.tsx (EXISTING: Admin candidate preview)
│       └── (existing AuthModal, HelpdeskApp remain with fixes)
├── context/
│   └── AuthContext.tsx      (FIXED: Guard authenticated API calls, remove switchDemoRole)
├── lib/
│   ├── api.ts              (UNCHANGED: apiClient with Bearer token interceptor)
│   ├── types.ts            (UNCHANGED: TypeScript interfaces)
│   ├── domainForms.ts      (NEW: Domain-specific form field definitions)
│   └── colors.ts           (NEW: Domain color palette map)
├── package.json
└── public/
```

### Database Schema Changes

**Migration: Add details_snapshot to ServiceRequest**

```python
# apps/requests/migrations/0003_servicerequest_details_snapshot.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('requests', '0002_servicerequest_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicerequest',
            name='details_snapshot',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text="Structured domain-specific details collected during request creation"
            ),
        ),
    ]
```

---

## Phase A: Authentication Initialization Fix

### Changes to Frontend

**File: `frontend/context/AuthContext.tsx`**

Current flow (BROKEN):
```
1. initAuth runs on mount
2. Check localStorage for token
3. Call apiOrganizations.list() → 401 if no user yet
4. Set org state
5. Try to call apiAuth.getMe()
```

Fixed flow:
```
1. initAuth runs on mount
2. Check localStorage for token
3. IF token exists: call apiAuth.getMe() with token
4. IF getMe() succeeds: set user state
5. THEN call apiOrganizations.list() (now authenticated)
6. IF getMe() fails: remove token, clear state, do not call org list
```

**Specific changes:**

1. Reorder initialization: token → me → organizations
2. Remove `switchDemoRole` function entirely
3. Change `login` to NOT hardcode a demo username
4. Change AuthModal password from hardcoded to from-input
5. Guard `apiOrganizations.list()` behind successful user authentication

**File: `frontend/components/helpdesk/Navbar.tsx`**

1. Remove the entire dark "Role Quick Switcher" bar
2. Remove `switchDemoRole` function calls
3. Fix missing `ZapIcon` import (remove or import from lucide-react)
4. Keep org selector (visible only when authenticated)

**File: `frontend/components/helpdesk/AuthModal.tsx`**

1. Remove the `role` state and selector from registration form
2. All self-registrations now get `role='USER'` hardcoded by backend

---

## Phase B: Idempotent Seed Command

**New file: `backend/apps/accounts/management/commands/seed_demo_data.py`**

Structure:
```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.employees.models import Employee, EmployeeRole, EmployeeSkill, EmployeeSchedule
from apps.services.models import ServiceDomain, PredefinedIssue
from apps.requests.models import ServiceRequest
from apps.assignments.models import Assignment
from apps.feedback.models import Feedback

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 1. Create organizations (get_or_create by name)
        # 2. Create super admin
        # 3. Create org admins
        # 4. Create service domains per org
        # 5. Create predefined issues
        # 6. Create employee roles
        # 7. Create employees with skills & schedules
        # 8. Create residents
        # 9. Create 15 historical completed requests with feedback
        # 10. Create 5 active/in-progress requests
        # 11. Create 3 urgent requests
```

**Key idempotency strategy:**

- Use `get_or_create()` with a `defaults={}` dict for all model instances
- Key on: username for users, (organization, name) for domains, etc.
- Never rely on IDs; always query by natural key
- If record exists, verify it has correct data (update if needed)
- Use `bulk_create(ignore_conflicts=True)` for large datasets if needed

---

## Phase C: Application Shell & Design System

**File: `frontend/app/globals.css`**

```css
/* Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Design System: Color Palette */
:root {
  /* Primary Brand */
  --color-primary: #6366f1;
  --color-primary-light: #e0e7ff;
  --color-primary-dark: #4f46e5;
  
  /* Neutrals */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-text-primary: #0f172a;
  --color-text-muted: #64748b;
  
  /* Status */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  
  /* Domain Colors */
  --color-electrical: #f59e0b;
  --color-plumbing: #3b82f6;
  --color-hvac: #06b6d4;
  --color-cleaning: #14b8a6;
  --color-carpentry: #b45309;
  --color-security: #ef4444;
  --color-it-support: #8b5cf6;
  --color-general: #64748b;
  
  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 2rem;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
}

* {
  font-family: var(--font-family);
}

body {
  background-color: var(--color-bg);
  color: var(--color-text-primary);
}

/* Override Bootstrap Color Scheme */
:root {
  --bs-primary: var(--color-primary);
  --bs-secondary: var(--color-text-muted);
  --bs-success: var(--color-success);
  --bs-warning: var(--color-warning);
  --bs-danger: var(--color-danger);
  --bs-light: var(--color-bg);
  --bs-dark: var(--color-text-primary);
}

/* Utility classes */
.text-muted-custom { color: var(--color-text-muted); }
.bg-primary-light { background-color: var(--color-primary-light); }

/* Domain Badge Colors */
.badge-electrical { background-color: var(--color-electrical) !important; }
.badge-plumbing { background-color: var(--color-plumbing) !important; }
.badge-hvac { background-color: var(--color-hvac) !important; }
/* ... etc for all domains ... */
```

**File: `frontend/components/helpdesk/HelpdeskApp.tsx`**

Update to render based on user role:
```typescript
if (user?.is_superuser) {
  return <SuperAdminPortal />;
} else if (role === 'ADMIN') {
  return <AdminPortal />;
} else if (role === 'EMPLOYEE') {
  return <EmployeePortal />;
} else {
  return <ResidentPortal />;
}
```

**File: `frontend/components/helpdesk/shared/Sidebar.tsx`** (NEW)

Sidebar component with navigation sections for Admin/Employee portals.

---

## Phase D: Dynamic Request Wizard

**New file: `frontend/lib/domainForms.ts`**

```typescript
export const domainFieldDefinitions = {
  Electrical: {
    fields: [
      { name: 'affected_equipment', label: 'Affected Equipment', type: 'text' },
      { name: 'affected_room', label: 'Affected Room/Area', type: 'text' },
      { name: 'power_available', label: 'Power Available?', type: 'boolean' },
      { name: 'burning_smell', label: 'Burning Smell?', type: 'boolean' },
      { name: 'sparks', label: 'Sparks?', type: 'boolean' },
      { name: 'when_started', label: 'When Did This Start?', type: 'text' },
      { name: 'safety_concern', label: 'Safety Concern?', type: 'boolean' },
      { name: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  Plumbing: { /* ... */ },
  // ... etc
};

export const locationFields = {
  RESIDENTIAL_COLONY: ['tower', 'floor', 'flat_number', 'room'],
  GATED_COMMUNITY: ['tower', 'floor', 'flat_number', 'room'],
  OFFICE_SPACE: ['building', 'floor', 'department', 'room'],
};
```

**New file: `frontend/components/helpdesk/wizard/RequestWizard.tsx`**

Multi-step form component handling all 6 steps.

---

## Phase E–J: Portal Components

Each portal (SuperAdmin, Admin, Employee, Resident) gets a new component file with:
- Sidebar navigation (Admin/Employee)
- KPI cards
- Data tables with search/filter/sort
- Request/assignment action buttons
- Real API data fetching (no mock data)
- Loading/error/empty states

---

## API Endpoints (Existing + New)

### Authentication
- `POST /api/auth/login/` — (existing) returns `{access, refresh, user}`
- `GET /api/auth/me/` — (existing) returns authenticated user profile
- `GET /api/auth/users/` — (existing UserViewSet, enhanced filtering)

### Organizations
- `GET /api/organizations/` — list orgs (IsAuthenticated)
- `POST /api/organizations/` — create org (IsAdminRole)
- `POST /api/organizations/{id}/activate/` — activate org
- `POST /api/organizations/{id}/deactivate/` — deactivate org
- `GET /api/organizations/org_types/` — return org type choices

### Service Domains
- `GET /api/services/domains/` — list domains
- `POST /api/services/domains/` — create domain (IsAdminRole)
- `GET /api/services/issues/` — list predefined issues
- `POST /api/services/issues/` — create issue (IsAdminRole)

### Service Requests
- `GET /api/requests/` — list requests (scoped to user/org)
- `POST /api/requests/` — create request (auto-assigns)
- `POST /api/requests/{id}/start_work/` — start work
- `POST /api/requests/{id}/complete_work/` — complete work
- `POST /api/requests/{id}/reopen/` — reopen if unresolved
- `GET /api/requests/{id}/candidates_preview/` — admin candidate inspector

### Assignments
- `POST /api/assignments/{id}/accept/` — employee accepts
- `POST /api/assignments/{id}/reassign/` — admin reassigns

### Feedback
- `POST /api/feedback/` — submit feedback (auto-reopens if unresolved)

### Analytics
- `GET /api/analytics/overview/` — org-scoped KPIs (IsAuthenticated)
- `GET /api/analytics/charts/` — org-scoped charts (IsAuthenticated)
- **NEW: `GET /api/analytics/platform/` — platform-wide KPIs (superuser only)**

### Employees
- `GET /api/employees/` — list employees
- `GET /api/employees/me/` — current employee profile
- `POST /api/employees/{id}/set_status/` — set employee status
- `PATCH /api/employees/{id}/toggle_availability/` — toggle availability

---

## Test Structure

**New test files/enhancements:**

1. `apps/accounts/tests.py` — Authentication, Authorization, Isolation
2. `apps/requests/tests.py` — Request creation, assignment trigger, status transitions
3. `apps/feedback/tests.py` — Feedback submit, reopen, SLA tracking
4. `apps/services/tests.py` — ServiceDomain CRUD, org isolation
5. `apps/accounts/management/commands/tests.py` — Seed command idempotency

**Backend test commands:**
```bash
python manage.py test --noinput
python manage.py check --database default
python manage.py makemigrations --check
```

**Frontend build:**
```bash
npm run build
```

---

## Correctness Properties (Enforced by Design)

1. **JWT Round-Trip**: Token from login successfully authenticates all subsequent API calls
2. **401 on Missing Token**: `GET /api/requests/` without Authorization header returns 401
3. **Resident Data Isolation**: Residents see only their own requests
4. **Cross-Org Isolation**: Users cannot access resources of other organizations
5. **Assignment Proximity**: Lower distance → higher suitability score (distance weighting = 50%)
6. **Idempotent Seed**: Running `seed_demo_data` N times = running once
7. **Automatic Assignment**: ServiceRequest creation triggers AssignmentService
8. **Ranker Stability**: DeterministicWeightedRanker is active; Keras model not loaded

---

## Dependencies (No New External Packages Required)

**Backend:** Already installed (djangorestframework, djangorestframework-simplejwt, psycopg2, django-cors-headers, django-filter)

**Frontend:** Already installed (Next.js, React, axios, Bootstrap, lucide-react)

**Frontend NEW: GSAP for animations** — `npm install gsap`

---

## File Summary: New Files Created This Phase

| Path | Purpose |
|------|---------|
| `.kiro/specs/intellidesk-phase3/requirements.md` | Requirements with EARS-pattern acceptance criteria |
| `.kiro/specs/intellidesk-phase3/design.md` | This technical design document |
| `backend/apps/accounts/management/commands/seed_demo_data.py` | Idempotent seed command |
| `frontend/lib/domainForms.ts` | Domain-specific form field definitions |
| `frontend/lib/colors.ts` | Domain color palette map |
| `frontend/components/helpdesk/wizard/RequestWizard.tsx` | Multi-step request form |
| `frontend/components/helpdesk/wizard/steps/*` | Individual step components |
| `frontend/components/helpdesk/wizard/domainForms/*` | Domain-specific form components |
| `frontend/components/helpdesk/shared/Sidebar.tsx` | Admin/Employee sidebar navigation |
| `frontend/components/helpdesk/shared/KPICard.tsx` | Reusable KPI card component |
| `frontend/components/helpdesk/portals/SuperAdminPortal.tsx` | Super Admin dashboard |
| (Redesigned portal components) | AdminPortal, EmployeePortal, ResidentPortal (substantial rewrites) |

---

## Implementation Notes

- **Do NOT use Tailwind CSS** — Bootstrap + CSS variables override
- **Do NOT add new Django dependencies** — keep requirements.txt as-is (add GSAP to package.json only)
- **Keep DeterministicWeightedRanker as active** — do not load or use KerasRankingModel
- **Preserve all 47 existing backend tests** — add new tests without removing old
- **Remove demo/debug UI** — role switcher, dev footer, hardcoded passwords
- **Guard all authenticated API calls** — check token validity before calling org/user/request data
- **Use get_or_create everywhere in seed** — guarantee idempotency
- **GSAP animations: subtle and fast** — page transitions, card entrances, modal opens
- **Color palette: domain-aware** — Electrical = amber, Plumbing = blue, etc.
- **Organization scoping: strict** — non-superusers see only their org's data

---

## Success Criteria

1. ✓ No 401 errors on authenticated API calls after login
2. ✓ `seed_demo_data` runs idempotently (no duplicates on repeated runs)
3. ✓ All three portals (Resident, Employee, Admin) render with new design
4. ✓ Request wizard with dynamic fields based on domain + org type
5. ✓ Automatic assignment works on request creation
6. ✓ All 47 existing tests still pass
7. ✓ Backend: `python manage.py check --database default` passes
8. ✓ Backend: `python manage.py makemigrations --check` shows no pending migrations
9. ✓ Backend: `python manage.py test --noinput` passes all tests
10. ✓ Frontend: `npm run build` completes with zero errors

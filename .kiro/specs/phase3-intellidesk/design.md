# Design Document — Phase 3: IntelliDesk Production Hardening

## Overview

Phase 3 ships IntelliDesk as a production-quality SaaS product. The backend is largely complete; the main backend work is wiring the feedback endpoint, completing the employee scorecard, hardening permission checks, and adding the test suite. The frontend requires a full redesign using Next.js 14 App Router with Tailwind CSS, replacing the monolithic prototype components with three distinct, role-scoped portals (Resident, Employee, Admin).

**Tech stack (unchanged):**
- Backend: Django 4.x / DRF / SimpleJWT / PostgreSQL
- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts, Lucide React, Axios

**Constraint:** No Redis, Celery, WebSockets, paid APIs, NLP, LLMs, or new ORM models beyond what Phase 2 already defined.

---

## Architecture

```
Browser
  └─ Next.js 14 App Router (frontend/)
       ├─ (auth)/login          → AuthPage
       ├─ (resident)/           → ResidentLayout + pages
       ├─ (employee)/           → EmployeeLayout + pages
       └─ (admin)/              → AdminLayout + pages

Django (backend/)
  ├─ /api/auth/        → Login, Register, Me
  ├─ /api/organizations/
  ├─ /api/services/    → ServiceDomain, PredefinedIssue CRUD
  ├─ /api/requests/    → ServiceRequest CRUD + lifecycle actions
  ├─ /api/assignments/ → Assignment CRUD + accept/reassign
  ├─ /api/employees/   → Employee CRUD + skills/schedules
  ├─ /api/feedback/    → Feedback create + list
  └─ /api/analytics/   → overview KPIs + charts data

Assignment Engine (backend/apps/ml_engine/)
  CandidateSelector → FeatureBuilder → RankingModelInterface
                                           ↑
                             DeterministicWeightedRanker (default)
                             KerasRankingModel (injectable, non-default)
```

---

## Backend Changes

### 1. Feedback Endpoint — Wire POST

`apps/feedback/urls.py` already registers `FeedbackViewSet`. The `create()` logic is implemented in `feedback/views.py` but the endpoint needs to be verified as included in the main `urls.py`. Confirm `path('feedback/', include('apps.feedback.urls'))` is present in `config/urls.py`.

The `create()` override:
- Validates request ownership
- Prevents duplicate feedback (OneToOne check)
- Auto-calculates `resolution_time_minutes` and `met_sla`
- If `is_resolved=False`: sets `status=REOPENED`, calls `AssignmentService.reassign_request`

No model changes needed; `Feedback` model is complete.

### 2. Analytics — Complete EmployeeScorecardView

```python
class EmployeeScorecardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        employee_id = pk or getattr(
            getattr(request.user, 'employee_profile', None), 'id', None
        )
        if not employee_id:
            return Response({'error': 'Employee profile not found.'}, status=404)

        emp = get_object_or_404(
            Employee.objects.select_related('user', 'role')
                            .prefetch_related('assignments__request__feedback'),
            pk=employee_id,
            organization=request.user.organization
        )
        # Re-use the per-employee computation already in AnalyticsService.get_charts_data
        # by extracting it into a private method, then calling it here.
        scorecard = AnalyticsService.get_employee_scorecard(emp)
        return Response(scorecard)
```

Extract `_employee_stats(emp)` helper from `get_charts_data` to avoid duplication.

### 3. Permission Hardening

All existing permission classes are correct. Verify `IsAdminRole` is applied to destructive actions on `ServiceDomainViewSet` and `PredefinedIssueViewSet` (already done in Phase 2). Verify `IsEmployeeRole` on `EmployeeScorecardView`.

Ensure `ServiceRequestViewSet.perform_create` ignores any `organization` field in the request body (it does — it reads from `user.organization`).

### 4. DB Query Optimization

Audit all ViewSet `get_queryset` methods for N+1 patterns. Key fixes:
- `FeedbackViewSet.get_queryset`: already uses `select_related`.
- `AnalyticsService.get_charts_data` employee loop: currently issues per-employee queries — refactor to use `prefetch_related('assignments__request__feedback')` on the queryset, then process in Python.
- `ServiceRequestViewSet`: already uses `prefetch_related('assignments__employee__user', ...)`.

### 5. New Test Modules

Add test files:
- `apps/accounts/tests_phase3.py` — auth tests
- `apps/requests/tests_phase3.py` — lifecycle + isolation tests
- `apps/feedback/tests.py` — feedback logic tests
- `apps/services/tests.py` — service domain CRUD permission tests

No existing tests in `apps/accounts/tests.py` or `apps/ml_engine/tests.py` should be modified.

---

## Frontend Architecture

### Directory Structure

```
frontend/
├── app/
│   ├── layout.tsx                  # Root layout with AuthProvider
│   ├── page.tsx                    # Redirect → /login
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx
│   ├── (resident)/
│   │   ├── layout.tsx              # ResidentLayout (top-nav, auth guard role=USER)
│   │   ├── page.tsx                # Resident home / request list
│   │   ├── requests/
│   │   │   ├── new/page.tsx        # Multi-step request creation
│   │   │   └── [id]/page.tsx       # Request detail + feedback
│   │   └── profile/page.tsx
│   ├── (employee)/
│   │   ├── layout.tsx              # EmployeeLayout (sidebar, auth guard role=EMPLOYEE)
│   │   ├── page.tsx                # Employee dashboard
│   │   ├── assignments/
│   │   │   ├── page.tsx            # Assignment queue
│   │   │   └── [id]/page.tsx       # Assignment detail
│   │   └── history/page.tsx
│   └── (admin)/
│       ├── layout.tsx              # AdminLayout (sidebar, auth guard role=ADMIN)
│       ├── page.tsx                # Admin dashboard (KPIs + charts)
│       ├── requests/
│       │   ├── page.tsx            # Request management table
│       │   └── [id]/page.tsx       # Request detail
│       ├── employees/
│       │   ├── page.tsx
│       │   ├── new/page.tsx
│       │   └── [id]/page.tsx
│       ├── services/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       └── users/
│           ├── page.tsx
│           └── new/page.tsx
├── components/
│   ├── ui/                         # Design system primitives
│   │   ├── Button.tsx
│   │   ├── Badge.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Modal.tsx
│   │   ├── Toast.tsx / ToastProvider.tsx
│   │   ├── Skeleton.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ErrorState.tsx
│   │   └── Table.tsx
│   ├── layout/
│   │   ├── AdminSidebar.tsx
│   │   ├── EmployeeSidebar.tsx
│   │   ├── ResidentNav.tsx
│   │   └── PageHeader.tsx
│   ├── resident/
│   │   ├── RequestCard.tsx
│   │   ├── NewRequestWizard.tsx
│   │   ├── FeedbackModal.tsx
│   │   └── RequestStatusBadge.tsx
│   ├── employee/
│   │   ├── AssignmentCard.tsx
│   │   ├── SlaCountdown.tsx
│   │   └── WorkloadBar.tsx
│   └── admin/
│       ├── KpiCard.tsx
│       ├── RequestsTable.tsx
│       ├── EmployeeTable.tsx
│       ├── CandidateInspectorModal.tsx
│       ├── DomainManagement.tsx
│       └── charts/
│           ├── RequestsByDomainChart.tsx
│           ├── DailyTrendChart.tsx
│           ├── PriorityChart.tsx
│           └── SatisfactionChart.tsx
├── context/
│   ├── AuthContext.tsx             # JWT storage, user profile, login/logout
│   └── ToastContext.tsx            # Global toast queue
├── hooks/
│   ├── useRequests.ts
│   ├── useEmployees.ts
│   ├── useAnalytics.ts
│   └── usePagination.ts
└── lib/
    ├── api.ts                      # Axios client + interceptors (existing, extended)
    └── types.ts                    # TypeScript types (existing, extended)
```

### Authentication Flow

```
AuthContext (context/AuthContext.tsx)
  - stores: accessToken, refreshToken, user: UserProfile | null
  - persists to localStorage under keys helpdesk_access_token, helpdesk_refresh_token
  - exposes: login(username, password), logout(), isAuthenticated, user

Axios interceptor (lib/api.ts)
  - request: attach Bearer token from localStorage
  - response: on 401 → attempt /auth/token/refresh/ → retry original request
              on refresh failure → call logout() → redirect /login
```

Route guard pattern (each layout):
```tsx
// (admin)/layout.tsx
'use client';
import { useAuth } from '@/context/AuthContext';
import { redirect } from 'next/navigation';

export default function AdminLayout({ children }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <Skeleton />;
  if (!user) redirect('/login');
  if (user.role !== 'ADMIN') redirect('/login');
  return <AdminSidebarLayout>{children}</AdminSidebarLayout>;
}
```

### Design System Tokens (Tailwind)

```js
// tailwind.config.js additions
colors: {
  primary: { 50: '#eff6ff', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8' },
  surface: { DEFAULT: '#ffffff', raised: '#f8fafc', sunken: '#f1f5f9' },
  border: { DEFAULT: '#e2e8f0', strong: '#cbd5e1' },
  text: { primary: '#0f172a', secondary: '#475569', muted: '#94a3b8' },
  status: {
    created:    '#94a3b8',
    queued:     '#f59e0b',
    assigned:   '#3b82f6',
    in_progress:'#8b5cf6',
    completed:  '#10b981',
    reopened:   '#f97316',
    cancelled:  '#ef4444',
  },
  priority: {
    low:      '#64748b',
    normal:   '#3b82f6',
    high:     '#f59e0b',
    urgent:   '#f97316',
    critical: '#ef4444',
  },
}
```

### API Client Extension

The existing `lib/api.ts` is extended to add:

```typescript
// Token refresh interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = localStorage.getItem('helpdesk_refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, { refresh });
          localStorage.setItem('helpdesk_access_token', data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return apiClient(originalRequest);
        } catch {
          // refresh failed — handled by AuthContext logout
        }
      }
    }
    return Promise.reject(error);
  }
);

// Additional API methods
export const apiUsers = {
  list: (params?) => apiClient.get('/users/', { params }).then(r => r.data?.results ?? r.data),
  create: (payload) => apiClient.post('/users/', payload).then(r => r.data),
  activate: (id) => apiClient.post(`/users/${id}/activate/`).then(r => r.data),
  deactivate: (id) => apiClient.post(`/users/${id}/deactivate/`).then(r => r.data),
  setPassword: (id, password) => apiClient.post(`/users/${id}/set_password/`, { password }).then(r => r.data),
};

export const apiServices = {
  // existing methods +
  updateDomain: (id, payload) => apiClient.patch(`/services/domains/${id}/`, payload).then(r => r.data),
  deleteDomain: (id) => apiClient.delete(`/services/domains/${id}/`),
  listIssues: (params?) => apiClient.get('/services/issues/', { params }).then(r => r.data?.results ?? r.data),
  updateIssue: (id, payload) => apiClient.patch(`/services/issues/${id}/`, payload).then(r => r.data),
  deleteIssue: (id) => apiClient.delete(`/services/issues/${id}/`),
};
```

---

## Component Specifications

### NewRequestWizard

A 4-step wizard managed by local state `{ step: 1|2|3|4, domainId, issueId, description, location, lat, lng, priority }`:

| Step | Content |
|------|---------|
| 1 | Domain icon grid — fetches `GET /api/services/domains/?is_active=true` |
| 2 | Issue selector — fetches `GET /api/services/issues/?domain={id}&is_active=true`; plus "Custom description" option |
| 3 | Details form — location name text input, optional coords, priority selector; priority pre-filled from selected issue's `default_priority` |
| 4 | Summary — confirm and submit `POST /api/requests/` |

On submit, show loading state, then success toast + navigate to request list.

### AssignmentCard (Employee)

Displays per-assignment card with:
- Domain icon + name
- Issue title (predefined or truncated custom description)  
- Priority badge (color from design system)
- SLA countdown: `(assigned_at + sla_hours_snapshot * 3600000) - now` rendered as `HH:MM remaining` with warning colour below 2 hours
- Distance badge: `{distance_km} km`
- Location name
- Status-appropriate actions: ASSIGNED → "Start Work", IN_PROGRESS → "Mark Complete"
- On action: optimistic UI update + API call + toast

### KpiCard (Admin)

```tsx
interface KpiCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  accentColor?: string;
}
```

Uses `Card` with `border-l-4` accent, large value number, smaller subtitle.

### Charts

All charts use Recharts. Responsive via `ResponsiveContainer width="100%" height={280}`:
- `RequestsByDomainChart`: `BarChart` with `Bar` fill by domain
- `DailyTrendChart`: `LineChart` with two lines (created, completed)
- `PriorityChart`: `BarChart` with priority-color fills
- `SatisfactionChart`: `BarChart` 1-5 star distribution

---

## Data Flow

### Request Creation + Auto-Assignment

```
Resident submits form
  → POST /api/requests/  (payload: domain, predefined_issue|custom_description, location, priority)
  → ServiceRequestViewSet.perform_create()
      → serializer.save(user, organization, lat, lng)
      → AssignmentService().auto_assign(request_obj)
          → CandidateSelector.get_eligible_candidates(req)
          → [FeatureBuilder.build_features(req, emp) for emp in candidates]
          → DeterministicWeightedRanker.rank_candidates(features_list)
          → Assignment.objects.create(... all snapshots ...)
          → request.status = ASSIGNED (or QUEUED if no candidates)
  → HTTP 201 with ServiceRequest + active_assignment nested
```

### Feedback → Reopen → Reassign

```
Resident submits feedback
  → POST /api/feedback/  (payload: request, is_resolved, rating, comments)
  → FeedbackViewSet.create()
      → validates ownership + no duplicate
      → calculates resolution_time_minutes, met_sla
      → Feedback.objects.create(...)
      → if not is_resolved:
          request.status = REOPENED
          AssignmentService().reassign_request(request, reason=comments)
              → exclude previous assignee
              → full pipeline again
              → new Assignment created
  → HTTP 201 with Feedback data
```

---

## API Contracts

### POST /api/auth/login/

**Request:**
```json
{ "username": "resident1", "password": "secret" }
```
**Response 200:**
```json
{
  "access": "<jwt_access>",
  "refresh": "<jwt_refresh>",
  "user": {
    "id": "uuid", "username": "resident1", "role": "USER",
    "role_display": "Resident / Customer",
    "organization": "uuid", "organization_details": { ... }
  }
}
```
**Response 400:** `{ "non_field_errors": ["Invalid credentials provided."] }`

### POST /api/requests/

**Request:**
```json
{
  "domain": "uuid",
  "predefined_issue": "uuid",       // optional
  "custom_description": "",          // required if no predefined_issue
  "location_name": "Block A, Unit 4",
  "latitude": 12.9300,              // optional
  "longitude": 77.6800,             // optional
  "priority": "HIGH"                // optional, default NORMAL
}
```
**Response 201:** Full `ServiceRequest` object including `active_assignment` nested.

### GET /api/requests/{id}/candidates_preview/

**Response 200:**
```json
{
  "request_id": "uuid",
  "domain": "Electrical",
  "candidate_count": 3,
  "candidates": [
    {
      "employee_id": "uuid",
      "employee_name": "Ali Hassan",
      "role_title": "Senior Electrician",
      "distance_km": 0.8,
      "suitability_score": 0.87,
      "current_active_jobs": 1,
      "domain_proficiency": 5,
      "historical_avg_rating": 4.6,
      "features": { ... }
    }
  ]
}
```

### POST /api/feedback/

**Request:**
```json
{
  "request": "uuid",
  "is_resolved": false,
  "rating": 2,
  "comments": "Technician did not fix the issue"
}
```
**Response 201:** Full `Feedback` object.
**Response 400:** `{ "error": "Feedback already submitted for this request." }`

### GET /api/analytics/overview/

**Response 200:** `OverviewKPIs` object (existing schema, no change).

### GET /api/analytics/charts/?days=14

**Response 200:** `ChartsData` object (existing schema, no change).

---

## Database Changes

No new migrations are required. All models were finalized in Phase 2. The only "change" is confirming the following indexes exist and adding any missing ones via a migration if needed:

| Table | Index | Purpose |
|-------|-------|---------|
| `service_requests` | `(organization, status, created_at)` | Admin list queries |
| `assignments` | `(employee, status)` | Employee queue queries |
| `feedback` | `(request)` — via OneToOne | Already enforced by OneToOneField |
| `users` | `(organization, role)` | User management scoping |

All these are already present in the existing model Meta classes.

---

## Security Considerations

1. **JWT secret**: Ensure `SIMPLE_JWT` `SIGNING_KEY` is set from environment variable, not hardcoded.
2. **CORS**: `CORS_ALLOWED_ORIGINS` in Django settings must include only the frontend origin; do not use `CORS_ALLOW_ALL_ORIGINS=True` in production.
3. **Token storage**: `localStorage` is used for convenience; if XSS risk is later deemed unacceptable, migrate to `httpOnly` cookies. For Phase 3 scope, localStorage is acceptable.
4. **Organization field stripping**: `perform_create` in all ViewSets explicitly ignores `organization` from request body for non-superusers. This must not be removed.
5. **Password reset**: Admin `set_password` action uses `user.set_password()` which properly hashes; it does not store plaintext.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do.*

### Property 1: Self-registration privilege escalation is impossible

*For any* role value in `{ADMIN, EMPLOYEE}`, a POST to `/api/auth/register/` with that role value SHALL return HTTP 403 and SHALL NOT create a user with an elevated role.

**Validates: Requirements 1.6**

---

### Property 2: Organization isolation for list endpoints

*For any* authenticated user in organization A (non-superuser), a GET request to any of the list endpoints (`/api/requests/`, `/api/employees/`, `/api/feedback/`, `/api/services/domains/`, `/api/users/`) SHALL return zero records that belong to organization B.

**Validates: Requirements 2.1, 2.2**

---

### Property 3: Organization isolation for detail endpoints

*For any* resource record (ServiceRequest, Employee, Feedback, ServiceDomain, User) that belongs to organization B, a GET/PATCH/DELETE request by an authenticated non-superuser in organization A SHALL return HTTP 403 or HTTP 404.

**Validates: Requirements 2.2**

---

### Property 4: Auto-assignment fires on every new valid request

*For any* ServiceRequest created via POST when at least one eligible candidate exists, the resulting request SHALL have status `ASSIGNED` and there SHALL exist exactly one `Assignment` record with that request's ID and status `ASSIGNED`.

**Validates: Requirements 3.5, 3.7, 5.1**

---

### Property 5: CandidateSelector hard-filter invariant

*For any* ServiceRequest, the list returned by `CandidateSelector.get_eligible_candidates(request, check_schedule=False)` SHALL NOT contain any employee that violates at least one of: same organization as request, status=ACTIVE, is_available=True, has a skill entry for the request's domain, active assignment count < max_active_assignments.

**Validates: Requirements 2.3, 5.3, 17.7**

---

### Property 6: Availability flag forced to False on INACTIVE/OFF_DUTY

*For any* Employee, after a successful `POST /api/employees/{id}/set_status/` with `status` in `{INACTIVE, OFF_DUTY}`, the Employee record's `is_available` field SHALL be `False`.

**Validates: Requirements 9.4**

---

### Property 7: Feedback SLA calculation correctness

*For any* Feedback record created by the system, given `resolution_time_minutes = (completed_at - created_at).total_seconds() / 60` and `sla_limit = domain.sla_hours * 60`, the `met_sla` field SHALL equal `resolution_time_minutes <= sla_limit`.

**Validates: Requirements 12.3**

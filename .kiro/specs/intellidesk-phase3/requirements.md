# Requirements Document

## Introduction

IntelliDesk Phase 3 is a complete production-ready build of an intelligent workforce helpdesk SaaS platform. The system serves three distinct user portals — Resident, Employee, and Admin — backed by a Django/PostgreSQL REST API with JWT authentication, and a Next.js frontend. Phase 3 addresses a critical authentication initialization bug, establishes a comprehensive demo data seed command, redesigns all three portals with a professional UI, introduces a Super Admin platform dashboard, replaces the request creation modal with a multi-step wizard, connects all UI to real API data, and completes a full backend + frontend test suite that must pass cleanly.

The existing codebase has 47 passing backend tests, Django REST Framework with JWT auth (`djangorestframework-simplejwt`), and a `DeterministicWeightedRanker` as the active ranking engine behind the `RankingModelInterface` abstraction. A Keras model file exists on disk but is NOT the production ranker.

---

## Glossary

- **AuthContext**: The React context provider (`frontend/context/AuthContext.tsx`) that manages authentication state (user, token, organization) across the Next.js application.
- **apiClient**: The axios instance in `frontend/lib/api.ts` that attaches the Bearer token from localStorage to all outbound API requests.
- **JWT Token**: A JSON Web Token returned by `POST /api/auth/login/` as `{ access, refresh, user }`. Stored in `localStorage` under the key `helpdesk_access_token`.
- **initAuth**: The initialization routine in AuthContext that runs on application load to restore auth state from localStorage.
- **RankingModelInterface**: The abstract Python interface (`apps/ml_engine/interfaces.py`) that all ranking engines implement. Currently backed by `DeterministicWeightedRanker`.
- **DeterministicWeightedRanker**: The active production ranker (`apps/ml_engine/placeholder_ranker.py`) that scores candidates using weighted factors: distance (50%), workload (20%), proficiency (15%), experience (8%), historical performance (7%).
- **AssignmentService**: The Django service that, on `ServiceRequest` creation, calls `CandidateSelector` then the active `RankingModelInterface` to auto-assign the best eligible employee.
- **CandidateSelector**: The eligibility filter (`apps/ml_engine/selector.py`) that enforces hard business rules (org isolation, domain skill, ACTIVE status, availability, workload capacity, shift schedule) before ranking.
- **seed_demo_data**: The Django management command at `apps/accounts/management/commands/seed_demo_data.py` that creates all demo organizations, users, employees, service domains, predefined issues, and historical requests idempotently.
- **Resident**: A user with `role = 'USER'` who can create service requests and submit feedback. Self-registration is restricted to this role.
- **Employee**: A user with `role = 'EMPLOYEE'` who is assigned and works on service requests.
- **Admin**: A user with `role = 'ADMIN'` who manages an organization's users, employees, service domains, and views analytics.
- **Super Admin**: A Django `is_superuser=True` user who can view cross-organization platform KPIs and manage all organizations.
- **ServiceRequest**: A maintenance/service request raised by a Resident, linked to an organization, domain, and optionally a predefined issue. The `custom_description` field holds a JSON-encoded string of structured domain-specific detail fields. A new `details_snapshot` JSONField also stores this structured data.
- **PredefinedIssue**: A catalog entry for a common problem within a ServiceDomain (e.g., "Power socket not working" under Electrical).
- **ServiceDomain**: A service category (e.g., Electrical, Plumbing) scoped to an organization, with an SLA target in hours.
- **SLA**: Service Level Agreement target — the maximum hours within which a service request should be resolved, defined per ServiceDomain.
- **Request Wizard**: The multi-step full-screen flow (Steps: Service → Problem → Details → Location → Priority → Review) that replaces the legacy request creation modal.
- **Organization**: A tenant entity (e.g., a gated community, residential colony, or office space). All data is scoped to organizations.
- **details_snapshot**: A new `JSONField` on `ServiceRequest` that stores structured domain-specific input collected in the Request Wizard Step 3.
- **Platform KPIs**: Cross-organization aggregate statistics visible only to Super Admin users via `GET /api/analytics/platform/`.

---

## Requirements

### Requirement 1: Authentication Initialization Fix (Phase A)

**User Story:** As a user, I want the application to correctly restore my authenticated session on page load without triggering unauthorized API calls, so that I land on the correct portal immediately after login or browser refresh without seeing 401 errors.

#### Acceptance Criteria

1. WHEN the application loads and no token exists in `localStorage`, THE `AuthContext` SHALL NOT call any authenticated API endpoints (including `GET /api/organizations/`).
2. WHEN the application loads and a token exists in `localStorage`, THE `AuthContext` SHALL call `GET /api/auth/me/` with the stored token before calling any other authenticated endpoint.
3. WHEN `GET /api/auth/me/` returns a successful response, THE `AuthContext` SHALL set the authenticated user state and then load organization data associated with the user.
4. WHEN `GET /api/auth/me/` returns a 401 or error response, THE `AuthContext` SHALL remove the token from `localStorage`, clear authentication state, and set `isLoading` to false without making further authenticated API calls.
5. WHEN a user completes login via `POST /api/auth/login/`, THE `AuthContext` SHALL store the returned `access` token in `localStorage`, set user state from the returned `user` object, and render the correct portal based on `user.role` without a page reload.
6. WHEN a user triggers logout, THE `AuthContext` SHALL remove `helpdesk_access_token` from `localStorage`, clear `user` and `token` state, and a subsequent `GET /api/requests/` call without a token SHALL return HTTP 401.
7. THE `AuthContext` SHALL NOT expose a `switchDemoRole` function or any demo role-switching infrastructure.

---

### Requirement 2: Navbar and UI Cleanup (Phase A/C)

**User Story:** As a user, I want a clean, professional navigation interface without developer debug tools, so that the application looks and behaves like a production SaaS product.

#### Acceptance Criteria

1. THE `Navbar` component SHALL NOT render a "Role Quick Switcher" bar or any demo role-switching UI elements.
2. THE `Navbar` component SHALL import `ZapIcon` (or any icon it uses) explicitly from `lucide-react` before referencing it.
3. THE `AuthModal` registration form SHALL NOT render a role selection dropdown; all self-registered users SHALL be created with the `USER` (Resident) role.
4. THE frontend footer SHALL NOT display internal technical implementation details such as "Normalized PostgreSQL Schema".
5. WHEN a user is authenticated as `ADMIN`, THE application SHALL render the Admin portal sidebar navigation.
6. WHEN a user is authenticated as `EMPLOYEE`, THE application SHALL render the Employee portal sidebar navigation.
7. WHEN a user is authenticated as `USER` (Resident), THE application SHALL render the Resident portal layout.
8. WHEN a user is authenticated as a superuser (`is_superuser=True`), THE application SHALL render the Super Admin portal.

---

### Requirement 3: Idempotent Demo Data Seed Command (Phase B)

**User Story:** As a developer, I want to run a single management command to populate the database with realistic demo data, so that I can immediately test all portal features without manually creating records.

#### Acceptance Criteria

1. THE `seed_demo_data` Command SHALL create three organizations using `get_or_create`: "Green Valley Residency" (GATED_COMMUNITY, Sector 62 Noida), "Sunrise Colony" (RESIDENTIAL_COLONY, Rohini Delhi), and "TechPark Business Center" (OFFICE_SPACE, Koramangala Bengaluru).
2. THE `seed_demo_data` Command SHALL create user accounts for `superadmin`, `colonyadmin`, `sunriseadmin`, `techparkadmin`, and all specified employee and resident users using `get_or_create` by `username`.
3. THE `seed_demo_data` Command SHALL create employee profiles with skills, schedule entries, and locations for all 15 specified employees across the three organizations.
4. THE `seed_demo_data` Command SHALL create service domains with the specified SLA hours for each organization using `get_or_create` by `(organization, name)`.
5. THE `seed_demo_data` Command SHALL create predefined issues (5–7 per domain per organization) using `get_or_create`.
6. THE `seed_demo_data` Command SHALL create 15 completed `ServiceRequest` records with associated `Feedback` (ratings 3–5, SLA met/missed mix) using realistic timestamps within the past 30 days.
7. THE `seed_demo_data` Command SHALL create 5 active or in-progress service requests and 3 urgent requests.
8. WHEN the `seed_demo_data` Command is run a second time, THE Command SHALL NOT create any duplicate organizations, users, employees, service domains, predefined issues, or requests.
9. FOR ALL seed runs N ≥ 1, running `seed_demo_data` N times SHALL produce the same database state as running it once (idempotency property).

---

### Requirement 4: Design System and Application Shell (Phase C)

**User Story:** As a user, I want a consistent, professional SaaS visual design across all portals, so that the application presents a trustworthy and polished user experience.

#### Acceptance Criteria

1. THE application SHALL apply the Inter font loaded from Google Fonts as the global base font.
2. THE application SHALL use the defined color palette: primary `#6366f1`, background `#f8fafc`, surface `#ffffff`, border `#e2e8f0`, text-primary `#0f172a`, text-muted `#64748b`, success `#10b981`, warning `#f59e0b`, danger `#ef4444`.
3. THE Admin and Employee portals SHALL use a sidebar navigation pattern instead of a top navbar layout.
4. THE Resident portal SHALL use a centered card-based layout.
5. WHEN CSS overrides are applied to Bootstrap, THE System SHALL use CSS custom variables (`--bs-primary`, `--color-primary`, etc.) scoped globally so that Bootstrap components inherit the new palette without duplicating declarations.

---

### Requirement 5: Super Admin Portal (Phase D)

**User Story:** As a platform super administrator, I want a dedicated dashboard to monitor all organizations and platform-wide KPIs, so that I can oversee the health of the entire IntelliDesk platform.

#### Acceptance Criteria

1. WHEN a user with `is_superuser=True` is authenticated, THE System SHALL render the Super Admin portal with platform KPI cards showing: total organizations, active organizations, total users, total employees, total requests, completion rate, average resolution time, and overall satisfaction rating.
2. THE Super Admin Portal SHALL display an organizations table with columns: name, type, user count, employee count, active request count, status, and action buttons.
3. THE Super Admin Portal SHALL display a users management table with search and filter capabilities by organization, role, and status.
4. THE Super Admin Portal SHALL display platform analytics charts: requests across organizations, requests by domain, and request status distribution.
5. THE `GET /api/analytics/platform/` endpoint SHALL require `is_superuser=True` and return cross-organization aggregate statistics including total organizations, users, employees, requests, completion rate, average resolution time, and overall satisfaction.
6. IF a non-superuser requests `GET /api/analytics/platform/`, THEN THE System SHALL return HTTP 403.
7. THE `UserViewSet` at `/api/auth/users/` SHALL support filtering by `organization`, `role`, and `is_active` query parameters when accessed by a superuser.

---

### Requirement 6: Dynamic Request Creation Wizard (Phase E)

**User Story:** As a resident, I want a guided multi-step form when creating a service request, so that I can provide structured, domain-specific information that helps the maintenance team resolve my issue faster.

#### Acceptance Criteria

1. THE Request Wizard SHALL present steps in sequence: (1) Service Domain, (2) Problem Selection, (3) Domain-Specific Details, (4) Location, (5) Priority, (6) Review and Submit.
2. WHEN a resident opens the Request Wizard (Step 1), THE Wizard SHALL display only service domains that are active (`is_active=True`) for the resident's organization.
3. WHEN a resident selects a domain in Step 1, THE Wizard SHALL populate Step 2 with predefined issues for that domain plus an "Other / Custom" option.
4. WHEN a resident is on Step 3 (Details) and the selected domain is "Electrical", THE Wizard SHALL render the following fields: `affected_equipment`, `affected_room`, `power_available` (boolean), `burning_smell` (boolean), `sparks` (boolean), `when_started`, `safety_concern` (boolean), `description`.
5. WHEN a resident is on Step 3 and the selected domain is "Plumbing", THE Wizard SHALL render: `fixture`, `severity`, `water_flowing` (boolean), `water_supply_affected` (boolean), `affected_room`, `when_started`, `description`.
6. WHEN a resident is on Step 3 and the selected domain is "HVAC / AC", THE Wizard SHALL render: `ac_type`, `room`, `cooling_severity`, `leakage` (boolean), `noise` (boolean), `smell` (boolean), `when_started`, `description`.
7. WHEN a resident is on Step 3 and the selected domain is "Cleaning", THE Wizard SHALL render: `area_type`, `approximate_size`, `cleaning_type`, `preferred_time`, `special_requirements`, `description`.
8. WHEN a resident is on Step 3 and the selected domain is "Carpentry", THE Wizard SHALL render: `furniture_item`, `damage_problem`, `material`, `severity`, `location_detail`, `description`.
9. WHEN a resident is on Step 3 and the selected domain is "Security", THE Wizard SHALL render: `incident_type`, `location_detail`, `incident_time`, `safety_concern` (boolean), `description`.
10. WHEN a resident is on Step 3 and the selected domain is "IT Support", THE Wizard SHALL render: `device`, `os`, `hardware_or_software`, `problem_type`, `error_description`, `when_started`, `location_detail`, `description`.
11. WHEN a resident is on Step 3 and the selected domain is "General Maintenance", THE Wizard SHALL render: `asset_item`, `problem_category`, `location_detail`, `when_started`, `description`.
12. WHEN a resident is on Step 4 (Location) and the organization type is `GATED_COMMUNITY` or `RESIDENTIAL_COLONY`, THE Wizard SHALL render location fields: Tower, Floor, Flat Number.
13. WHEN a resident is on Step 4 and the organization type is `OFFICE_SPACE`, THE Wizard SHALL render location fields: Building, Floor, Department.
14. WHEN the resident submits the wizard (Step 6), THE System SHALL serialize the Step 3 structured data as a JSON string into `ServiceRequest.custom_description` AND store it in the new `ServiceRequest.details_snapshot` JSONField.
15. THE `ServiceRequest` model SHALL have a `details_snapshot` JSONField (with `default=dict`, `blank=True`) backed by a database migration.
16. WHEN an employee views a completed or in-progress request, THE Employee Portal SHALL parse and display the `details_snapshot` fields in a human-readable structured format.

---

### Requirement 7: Resident Dashboard Redesign (Phase F)

**User Story:** As a resident, I want a clean, informative dashboard that shows my requests with key details at a glance, so that I can track the status of my issues without digging through menus.

#### Acceptance Criteria

1. THE Resident Dashboard SHALL display a list of the authenticated resident's service requests as domain-colored cards showing: domain badge, issue title, priority badge, location, status badge, assigned employee name and phone, distance, and SLA countdown.
2. THE Resident Dashboard SHALL display a prominent "New Request" button that launches the Request Wizard.
3. WHEN a resident selects a request card, THE System SHALL display a full request detail view including: complete status timeline, employee contact information, domain-specific details (parsed from `details_snapshot`), and a feedback form if the request is COMPLETED.
4. WHEN a resident completes a feedback form, THE System SHALL call `POST /api/feedback/` with `request`, `is_resolved`, `rating`, and `comments` fields, and update the request state accordingly.
5. WHEN the authenticated resident has no service requests, THE Resident Dashboard SHALL display an empty-state illustration with a prompt to create the first request.
6. THE Resident Dashboard SHALL fetch request data exclusively from `GET /api/requests/` with real API data; no mock or hardcoded data SHALL be present.

---

### Requirement 8: Employee Portal Redesign (Phase G)

**User Story:** As an employee, I want a task-focused dashboard with clear action buttons, so that I can efficiently manage my assigned work throughout the day.

#### Acceptance Criteria

1. THE Employee Portal SHALL have sidebar navigation with sections: Dashboard, My Tasks, History, and Profile.
2. THE Employee Dashboard SHALL display active assignment cards showing: priority badge, location, resident contact, distance, SLA countdown, and "Start Work" / "Complete Work" action buttons.
3. THE Employee Dashboard SHALL highlight urgent assignments visually distinct from normal-priority assignments.
4. THE Employee History page SHALL display a table of completed assignments including the resident rating received for each.
5. THE Employee Profile page SHALL display the employee's skills, schedule, and cumulative performance statistics.
6. WHEN an employee clicks "Start Work", THE System SHALL call `POST /api/requests/{id}/start_work/` and update the assignment card status.
7. WHEN an employee clicks "Complete Work", THE System SHALL call `POST /api/requests/{id}/complete_work/` and move the assignment to the History view.
8. THE Employee Portal SHALL fetch all data exclusively from real API endpoints; no mock or hardcoded data SHALL be present.

---

### Requirement 9: Admin Portal Redesign (Phase H)

**User Story:** As an organization administrator, I want a comprehensive management portal with KPI dashboards, workforce management, and service configuration, so that I can operate the helpdesk efficiently.

#### Acceptance Criteria

1. THE Admin Portal SHALL have sidebar navigation with sections: Dashboard, Requests, Workforce, Services, Users, and Reports.
2. THE Admin Dashboard SHALL display KPI cards for: total requests, open requests, in-progress requests, completed requests, urgent requests, SLA compliance rate, average rating, and available employees count.
3. THE Requests page SHALL display a sortable, filterable, and searchable table with columns: domain, issue title, resident name, priority badge, status badge, assigned employee, created date, and SLA countdown.
4. THE Workforce page SHALL display employee cards with: availability status, current workload (active / max), skills list, and a quick-toggle for availability.
5. THE Services page SHALL support CRUD operations for service domains (name, SLA hours, active toggle) and predefined issues within each domain.
6. THE Users page SHALL allow the admin to list, create, and deactivate user accounts within their organization.
7. THE Reports page SHALL display charts for: request distribution by domain, priority distribution, and daily request trend over the past 14 days.
8. THE Admin Portal SHALL fetch all data exclusively from real API endpoints; no mock or hardcoded data SHALL be present.

---

### Requirement 10: API Data Integration (Phase I)

**User Story:** As a user of any portal, I want all displayed data to come from the live backend API, so that the information I see is accurate and up to date.

#### Acceptance Criteria

1. THE System SHALL NOT contain any hardcoded mock data arrays used to populate portal UI in production code paths.
2. WHEN an API call returns a paginated response, THE frontend component SHALL handle both paginated (`{ results: [...], count: N }`) and non-paginated array responses correctly.
3. WHEN an API call fails, THE frontend component SHALL display an appropriate error state rather than crashing or showing stale data.
4. WHEN API data is loading, THE frontend component SHALL display a loading skeleton or spinner so the user understands data is being fetched.

---

### Requirement 11: Performance Optimizations (Phase J)

**User Story:** As a developer and end user, I want the backend to execute efficient database queries and the frontend to avoid redundant API calls, so that the application is fast and scalable.

#### Acceptance Criteria

1. THE `AnalyticsService.get_charts_data` method SHALL compute employee feedback statistics using a single aggregated query (e.g., `annotate` + `Avg`) rather than a Python loop that issues individual feedback queries per employee.
2. WHEN `ServiceRequest` querysets are returned by API views, THE Django view SHALL use `select_related` for `organization`, `user`, `domain`, and `predefined_issue` to eliminate N+1 queries.
3. WHEN `Assignment` querysets are returned by API views, THE Django view SHALL use `select_related` for `request`, `employee`, `employee__user` to eliminate N+1 queries.
4. THE React components SHALL NOT trigger duplicate `useEffect` calls for the same API endpoint on initial mount.

---

### Requirement 12: Test Suite Completion (Phase K)

**User Story:** As a developer, I want a comprehensive automated test suite that covers authentication, authorization, data isolation, business logic, and seed command correctness, so that regressions are caught before deployment.

#### Acceptance Criteria

1. THE backend test suite SHALL include `AuthenticationTest` cases verifying: login success returns `{ access, refresh, user }`, login failure with wrong credentials returns HTTP 401, and `GET /api/auth/me/` with a valid token returns the correct user profile.
2. THE backend test suite SHALL include `AuthorizationTest` cases verifying: a Resident user cannot access `GET /api/analytics/overview/`, and an Employee user cannot access admin-only endpoints.
3. THE backend test suite SHALL include `OrganizationIsolationTest` cases verifying: a user in Organization A cannot read `ServiceRequest` records belonging to Organization B.
4. THE backend test suite SHALL include `ServiceRequestAPITest` cases verifying: a Resident can create a request, the request transitions through valid status states, and creating a request triggers `AssignmentService` execution.
5. THE backend test suite SHALL include `FeedbackTest` cases verifying: submitting feedback on a COMPLETED request with `is_resolved=False` triggers a request reopen, and a resident can submit exactly one feedback per request.
6. THE backend test suite SHALL include `ServiceDomainCRUDTest` cases verifying: an Admin can create and update service domains within their organization.
7. THE backend test suite SHALL include `SeedCommandTest` verifying: running `seed_demo_data` twice produces no duplicate records (idempotency).
8. WHEN `python manage.py check --database default` is run, THE System SHALL produce no errors.
9. WHEN `python manage.py makemigrations --check` is run, THE System SHALL report no pending migrations.
10. WHEN `python manage.py test --noinput` is run, THE System SHALL report all tests passing with zero failures.
11. WHEN `npm run build` is run in the frontend directory, THE build SHALL complete successfully with zero TypeScript or build errors.

---

### Requirement 13: JWT Authentication Correctness Properties

**User Story:** As a security engineer, I want the JWT authentication flow to be correct and consistent end-to-end, so that only authenticated users with valid tokens can access protected resources.

#### Acceptance Criteria

1. FOR ALL valid credentials submitted to `POST /api/auth/login/`, THE System SHALL return an `access` JWT token that successfully authenticates `GET /api/requests/` without returning HTTP 401 (round-trip authentication property).
2. WHEN `GET /api/requests/` is called without an `Authorization` header, THE System SHALL return HTTP 401.
3. FOR ALL authenticated residents, `GET /api/requests/` SHALL return only the requests where `request.user_id == authenticated_user.id` (resident data isolation property).
4. FOR ALL authenticated users belonging to organization A, THE System SHALL return HTTP 403 or HTTP 404 when they attempt to access a `ServiceRequest`, `Employee`, `ServiceDomain`, or `Feedback` record belonging to organization B (cross-organization isolation property).

---

### Requirement 14: Assignment Engine Correctness Properties

**User Story:** As an operations engineer, I want the assignment engine to behave correctly and consistently, so that every new request is automatically assigned to the best eligible employee.

#### Acceptance Criteria

1. WHEN a `ServiceRequest` is created with status `CREATED`, THE `AssignmentService` SHALL automatically execute and, if eligible candidates exist, create an `Assignment` record linking the request to the highest-ranked employee.
2. THE `DeterministicWeightedRanker` SHALL remain the active ranking engine behind `RankingModelInterface`; the Keras model file SHALL NOT be loaded or used in production request handling.
3. FOR ALL pairs of eligible employee candidates A and B where `distance_km(A) < distance_km(B)` and all other scoring factors are equal, THE `DeterministicWeightedRanker` SHALL assign `suitability_score(A) > suitability_score(B)` (proximity-first ranking property).
4. FOR ALL `ServiceRequest` creation events, THE `AssignmentService` SHALL only consider employees in the same organization as the request (tenant isolation in assignment).
5. WHEN `CandidateSelector.get_eligible_candidates` is called, THE Selector SHALL exclude employees whose `status` is `ON_LEAVE`, `OFF_DUTY`, or `INACTIVE`, regardless of their `is_available` flag.

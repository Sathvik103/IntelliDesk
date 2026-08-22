# Requirements Document — Phase 3: IntelliDesk Production Hardening

## Introduction

Phase 3 completes IntelliDesk by replacing the prototype frontend with a professional, role-specific SaaS UI, wiring all working backend APIs to real screens, enforcing genuine JWT authentication and RBAC, connecting the automated assignment engine end-to-end, completing the feedback loop, and exposing full service-domain management to admins. The 47 existing backend tests must continue to pass throughout.

---

## Glossary

- **System**: The IntelliDesk application (Django/DRF backend + Next.js 14 frontend).
- **Resident**: An authenticated user with role `USER` who raises and tracks service requests.
- **Employee**: An authenticated user with role `EMPLOYEE` who accepts and resolves assigned requests.
- **Admin**: An authenticated user with role `ADMIN` who manages operations, workforce, and configuration.
- **ServiceRequest**: A maintenance or support ticket raised by a Resident, linked to a ServiceDomain, with priority, location, and lifecycle status.
- **Assignment**: A record linking a ServiceRequest to the best-ranked eligible Employee, produced by the assignment engine.
- **AssignmentEngine**: The pipeline consisting of CandidateSelector → FeatureBuilder → RankingModelInterface → AssignmentService.
- **RankingModel**: The pluggable interface (`RankingModelInterface`) implemented by `DeterministicWeightedRanker` by default; `KerasRankingModel` is an available but non-default alternative.
- **Feedback**: A post-completion survey (resolved yes/no, rating 1–5, optional comment) submitted by the Resident.
- **ServiceDomain**: A category of work (e.g., Electrical, Plumbing) with an associated SLA in hours.
- **PredefinedIssue**: A common issue template within a ServiceDomain with a default priority.
- **OrgIsolation**: The invariant that all data operations are scoped to the user's Organization.
- **JWT Token**: An access/refresh token pair issued by SimpleJWT on successful login.
- **AuthContext**: The React context that stores and provides token, user profile, and role to frontend components.
- **AppShell**: The top-level layout wrapper that enforces authentication guards and renders the correct portal per role.
- **Toast**: A transient in-app notification (success/error/info) shown after user actions.
- **Skeleton**: A loading placeholder shown while data is being fetched.

---

## Requirements

### Requirement 1 — Authentication

**User Story:** As any user, I want to log in with a username and password so that I can access the application securely with my role-appropriate interface.

#### Acceptance Criteria

1. WHEN a user submits valid credentials, THE System SHALL return a JWT access token, a refresh token, and the full user profile including role and organization.
2. WHEN a user submits invalid credentials, THE System SHALL return HTTP 401 with a descriptive error message and SHALL NOT issue any token.
3. WHEN an unauthenticated browser request reaches any protected frontend route, THE System SHALL redirect the user to the login page.
4. WHEN a user logs out, THE System SHALL clear the stored JWT tokens from the browser and redirect to the login page.
5. WHEN the JWT access token expires, THE System SHALL attempt a silent token refresh using the stored refresh token before presenting the login page.
6. THE System SHALL enforce the rule that public self-registration is limited to the `USER` (Resident) role; requests to self-register as `ADMIN` or `EMPLOYEE` SHALL return HTTP 403.
7. WHEN a Resident accesses any Admin or Employee route, THE System SHALL return HTTP 403.
8. WHEN an Employee accesses any Admin-only route, THE System SHALL return HTTP 403.
9. THE AppShell SHALL route authenticated users to the correct portal (Resident, Employee, or Admin) based on their role immediately after login, without requiring a manual navigation step.

---

### Requirement 2 — Organization Isolation

**User Story:** As an admin, I want every data operation to be automatically scoped to my organization so that tenant boundaries are never crossed.

#### Acceptance Criteria

1. THE System SHALL filter all ServiceRequest, Employee, Assignment, Feedback, ServiceDomain, and User querysets by the requesting user's `organization_id` unless the user is a superuser.
2. WHEN a user attempts to access a resource belonging to a different organization, THE System SHALL return HTTP 403 or HTTP 404 (no cross-tenant data leakage).
3. THE AssignmentEngine SHALL only consider candidates whose `organization_id` matches the ServiceRequest's `organization_id`.
4. WHEN creating a resource, THE System SHALL automatically attach the authenticated user's `organization_id` and SHALL ignore any `organization` field supplied in the request body by non-superusers.

---

### Requirement 3 — Service Request Creation (Resident)

**User Story:** As a Resident, I want to submit a service request through a guided form so that I can report a problem and have it routed to a skilled employee.

#### Acceptance Criteria

1. WHEN a Resident submits a new service request, THE System SHALL require a ServiceDomain selection and either a PredefinedIssue selection or a non-empty custom description.
2. WHEN a Resident submits a new service request, THE System SHALL accept a location name and optionally latitude/longitude coordinates; if coordinates are absent, THE System SHALL fall back to the organization's coordinates.
3. WHEN a Resident submits a new service request, THE System SHALL accept a priority value from the set {LOW, NORMAL, HIGH, URGENT, CRITICAL}; if absent, THE System SHALL default to NORMAL.
4. WHEN a Resident selects a PredefinedIssue, THE System SHALL pre-populate the priority field with the issue's `default_priority`, which the Resident may override.
5. WHEN a service request is successfully created, THE System SHALL immediately invoke the AssignmentEngine (`AssignmentService.auto_assign`) before returning the HTTP 201 response.
6. IF the AssignmentEngine finds no eligible candidates, THEN THE System SHALL set the request status to `QUEUED` and SHALL return HTTP 201 with the request data.
7. WHEN the AssignmentEngine assigns a candidate, THE System SHALL set the request status to `ASSIGNED` and record the Assignment with all snapshot columns populated.

---

### Requirement 4 — Request Tracking (Resident)

**User Story:** As a Resident, I want to see the current status and assigned employee for each of my requests so that I know what is happening.

#### Acceptance Criteria

1. THE System SHALL provide a request list endpoint that returns only requests belonging to the authenticated Resident, ordered by `created_at` descending.
2. WHEN a Resident retrieves a specific request, THE System SHALL include the active assignment details (employee name, role, distance, suitability score, status) if an assignment exists.
3. WHILE a request has status `COMPLETED` and no Feedback record exists, THE System SHALL indicate to the Resident that feedback can be submitted.
4. THE System SHALL display request status using the values: Created, Queued for Assignment, Assigned, In Progress, Completed, Reopened, Cancelled.

---

### Requirement 5 — Automated Assignment Engine

**User Story:** As an admin, I want every new service request to be automatically assigned to the best available employee so that no manual dispatching is required in normal operation.

#### Acceptance Criteria

1. THE AssignmentEngine SHALL use the pipeline: `CandidateSelector.get_eligible_candidates` → `FeatureBuilder.build_features` → `RankingModelInterface.rank_candidates` → select top-ranked → create `Assignment`.
2. THE System SHALL use `DeterministicWeightedRanker` as the default `RankingModelInterface` implementation; swapping to `KerasRankingModel` SHALL require only injecting a different implementation via `AssignmentService(ranking_model=...)` and SHALL NOT require changes to views, models, or URL routing.
3. THE CandidateSelector SHALL apply all hard eligibility rules: same organization, ACTIVE status, `is_available=True`, domain skill match, workload below `max_active_assignments`, and schedule compliance if schedules are configured.
4. WHEN the AssignmentEngine creates an Assignment, THE System SHALL populate all snapshot columns (geographic, skill, priority, SLA, workload, model version, full feature JSON).
5. IF a request is in QUEUED status, THEN THE System SHALL allow re-triggering assignment via `POST /api/requests/{id}/trigger_assignment/`, which is accessible to Admin users.
6. THE System SHALL provide `GET /api/requests/{id}/candidates_preview/` for admins to inspect ranked candidates and their feature vectors without creating an Assignment.

---

### Requirement 6 — Employee Operational Dashboard

**User Story:** As an Employee, I want a focused dashboard showing my active assignments so that I can efficiently work through my queue.

#### Acceptance Criteria

1. WHEN an Employee loads their portal, THE System SHALL display: active assignment count, urgent/critical assignment count, today's assignments, and the employee's own availability toggle.
2. WHEN an Employee views an assignment, THE System SHALL display: service domain, issue description, location name, priority badge, SLA deadline (derived from `sla_hours_snapshot` + `assigned_at`), distance in km, and requester contact.
3. WHEN an Employee clicks "Start Work" on an assigned request, THE System SHALL transition the ServiceRequest status to `IN_PROGRESS`, set `in_progress_at`, and update the Assignment status to `IN_PROGRESS`.
4. WHEN an Employee clicks "Mark Complete" on an in-progress request, THE System SHALL transition the ServiceRequest status to `COMPLETED`, set `completed_at`, and update the Assignment status to `COMPLETED`.
5. THE System SHALL provide an assignment history view listing all past assignments for the authenticated Employee with status, rating received, and SLA outcome.
6. WHEN an Employee uses the availability toggle, THE System SHALL call `PATCH /api/employees/{id}/toggle_availability/` and reflect the new state immediately.

---

### Requirement 7 — Admin Operations Dashboard

**User Story:** As an Admin, I want a real-time operations overview so that I can monitor service performance and workforce status.

#### Acceptance Criteria

1. WHEN an Admin loads the operations dashboard, THE System SHALL display KPIs from `AnalyticsService.get_overview_kpis()` scoped to the admin's organization: total requests, open requests, in-progress requests, completed requests, urgent+critical count, average resolution time, average rating, SLA compliance rate, and resolution rate.
2. WHEN an Admin loads the operations dashboard, THE System SHALL display workforce KPIs: total employees, available employees, unavailable employees, and employees at capacity.
3. THE System SHALL render charts powered by `AnalyticsService.get_charts_data()`: requests by domain (bar), requests by priority (bar), daily trend (line, last 14 days), satisfaction breakdown (bar), and workforce performance table.
4. THE System SHALL use real backend data exclusively; no mock or hard-coded statistics SHALL appear in the admin dashboard.
5. THE System SHALL support a `?days=N` query parameter on the charts endpoint for configurable trend window (default 14 days).

---

### Requirement 8 — Admin Request Management

**User Story:** As an Admin, I want to view and manage all service requests in my organization so that I can audit operations and handle exceptions.

#### Acceptance Criteria

1. THE System SHALL provide a paginated, filterable request list for admins scoped to their organization, supporting filters: domain, priority, status, and free-text search on description/location/user name.
2. WHEN an Admin views a specific request, THE System SHALL show the full timeline including assignment history, feedback, and all status transitions.
3. WHEN an Admin triggers re-assignment via `POST /api/requests/{id}/trigger_assignment/`, THE System SHALL execute the full AssignmentEngine pipeline and return the new Assignment or a QUEUED status.
4. WHEN an Admin cancels a request via `POST /api/requests/{id}/cancel/`, THE System SHALL set the ServiceRequest status to `CANCELLED` and cancel all active Assignments.
5. THE System SHALL allow admins to view the candidate inspector (`GET /api/requests/{id}/candidates_preview/`) showing ranked eligible employees with their feature vectors and scores.

---

### Requirement 9 — Admin Employee Management

**User Story:** As an Admin, I want to manage employee profiles, skills, schedules, and availability so that the workforce is correctly configured.

#### Acceptance Criteria

1. THE System SHALL provide CRUD for Employee profiles scoped to the admin's organization, including: name, role, experience years, max active assignments, and current location.
2. THE System SHALL provide CRUD for EmployeeSkill records, allowing admins to assign domain skills and proficiency levels (1–5) to employees.
3. THE System SHALL provide CRUD for EmployeeSchedule records, allowing admins to define working hours per day of week.
4. WHEN an Admin changes an Employee's status to `INACTIVE` or `OFF_DUTY` via `POST /api/employees/{id}/set_status/`, THE System SHALL automatically set `is_available=False`.
5. THE System SHALL allow bulk visibility of workforce availability across all employees in the admin's organization.

---

### Requirement 10 — Admin User Management

**User Story:** As an Admin, I want to create and manage user accounts in my organization so that residents and employees can access the system.

#### Acceptance Criteria

1. THE System SHALL provide CRUD for User accounts scoped to the admin's organization via `UserViewSet`.
2. WHEN an Admin creates a user, THE System SHALL automatically associate the user with the admin's organization.
3. THE System SHALL allow admins to activate or deactivate user accounts via `POST /api/users/{id}/activate/` and `POST /api/users/{id}/deactivate/`.
4. THE System SHALL allow admins to reset a user's password via `POST /api/users/{id}/set_password/` with minimum length of 6 characters.
5. IF an Admin attempts to deactivate their own account, THEN THE System SHALL return HTTP 400 with an error message.

---

### Requirement 11 — Service Domain & Issue Management (Admin)

**User Story:** As an Admin, I want to manage service domains and predefined issues so that the request catalog stays accurate.

#### Acceptance Criteria

1. THE System SHALL provide CRUD for ServiceDomain records scoped to the admin's organization, including: name, description, SLA hours, icon name, and active status.
2. THE System SHALL seed the following default ServiceDomain names for new organizations: Electrical, Plumbing, HVAC/AC, Cleaning, Carpentry, Security, IT Support, General Maintenance.
3. THE System SHALL provide CRUD for PredefinedIssue records linked to a ServiceDomain, including: title, default priority, estimated duration in minutes, and active status.
4. WHEN a ServiceDomain's `is_active` is set to False, THE System SHALL exclude it from the ServiceRequest creation domain selector returned to Residents.
5. WHEN a PredefinedIssue's `is_active` is set to False, THE System SHALL exclude it from the issue selector in the ServiceRequest creation form.

---

### Requirement 12 — Feedback Collection

**User Story:** As a Resident, I want to submit feedback after my request is completed so that I can rate the service and flag if the problem is still unresolved.

#### Acceptance Criteria

1. WHEN a ServiceRequest has status `COMPLETED` and no Feedback exists, THE System SHALL allow the Resident who raised it to submit feedback via `POST /api/feedback/`.
2. THE Feedback submission SHALL require: `is_resolved` (boolean), `rating` (integer 1–5); and optionally `comments` (text).
3. WHEN feedback is submitted, THE System SHALL automatically calculate `resolution_time_minutes` from `request.created_at` to `request.completed_at` and `met_sla` by comparing resolution time against `domain.sla_hours * 60`.
4. WHEN `is_resolved` is False, THE System SHALL reopen the ServiceRequest (status → `REOPENED`), clear `completed_at`, and invoke `AssignmentService.reassign_request` to assign a new employee excluding the previously assigned one.
5. IF a Feedback record already exists for a request, THEN THE System SHALL return HTTP 400 and SHALL NOT create a duplicate.
6. THE System SHALL expose Feedback records to Admins (org-scoped) and Employees (their own received feedbacks).

---

### Requirement 13 — UI Redesign: Application Shell & Design System

**User Story:** As any user, I want a professional, visually polished interface so that IntelliDesk feels like a serious SaaS product.

#### Acceptance Criteria

1. THE System SHALL replace the existing prototype component tree with a new App Router-based Next.js 14 structure that uses route groups to separate Resident, Employee, and Admin portals.
2. THE System SHALL implement a design system using Tailwind CSS utility classes with a consistent color palette (neutral grays, a single primary accent, semantic status colors), typography scale, and spacing tokens applied uniformly across all portals.
3. THE System SHALL implement a sidebar navigation layout for Admin and Employee portals, and a simplified top-navigation layout for the Resident portal.
4. THE System SHALL display skeleton loading states for all data-fetching components while API calls are in flight.
5. THE System SHALL display toast notifications for all user-initiated actions (submit, save, error, status change).
6. THE System SHALL display meaningful empty states with an icon and call-to-action for all list views when no data is present.
7. THE System SHALL display user-friendly error states when API calls fail, including a retry action where applicable.
8. THE System SHALL remove the development role-switcher, database/schema footer, and ML implementation details from all user-facing pages.
9. WHEN a user is not authenticated, THE System SHALL render only the login page; all other routes SHALL redirect to login.
10. THE System SHALL render correctly on viewport widths from 375px (mobile) to 1440px (desktop) with no horizontal overflow.

---

### Requirement 14 — Resident Portal UI

**User Story:** As a Resident, I want a simple, friendly interface focused on submitting and tracking my requests.

#### Acceptance Criteria

1. THE System SHALL render a Resident home screen showing the count of open requests and a prominent "New Request" button.
2. THE System SHALL render a multi-step request creation form: Step 1 — domain selection (icon grid); Step 2 — issue selection (predefined list + custom option); Step 3 — details (location, priority); Step 4 — confirmation.
3. THE System SHALL render a request list with status badges, priority indicators, and relative timestamps.
4. WHEN a Resident clicks a completed request that has no feedback, THE System SHALL display a feedback prompt.
5. THE System SHALL render the feedback form as a modal with a resolved/unresolved toggle, a star rating selector (1–5), and an optional comments textarea.

---

### Requirement 15 — Employee Portal UI

**User Story:** As an Employee, I want a task-oriented dashboard that surfaces my most urgent work clearly.

#### Acceptance Criteria

1. THE System SHALL render an Employee dashboard with four metric cards: Active Jobs, Urgent/Critical Jobs, Completed Today, and Availability Status.
2. THE System SHALL render an assignment queue sorted by priority (CRITICAL → URGENT → HIGH → NORMAL → LOW) with SLA countdown indicators.
3. WHEN an Employee views an assignment card, THE System SHALL display: domain icon, issue title, priority badge, distance badge, SLA remaining time, location name, and action buttons appropriate to the current status (Accept / Start Work / Mark Complete).
4. THE System SHALL render a history tab listing completed and cancelled assignments with rating received, resolution time, and SLA outcome badge.

---

### Requirement 16 — Admin Portal UI

**User Story:** As an Admin, I want a data-rich command center so that I can oversee all operations at a glance.

#### Acceptance Criteria

1. THE System SHALL render an Admin dashboard sidebar with sections: Dashboard, Requests, Employees, Service Domains, Users, and Settings (placeholder).
2. THE System SHALL render KPI metric cards in a 2×4 or responsive grid at the top of the dashboard page, loading data from `GET /api/analytics/overview/`.
3. THE System SHALL render four charts below the KPI cards: Requests by Domain (bar), Daily Trend (line), By Priority (bar), Satisfaction (bar), loaded from `GET /api/analytics/charts/`.
4. THE System SHALL render a workforce performance table below the charts listing each employee with: name, role, workload%, active jobs, completed, avg rating, SLA%, availability status.
5. THE System SHALL render a full-page requests management table with column headers, sortable columns, a filter bar, pagination, and per-row action menu (view, re-trigger assignment, cancel, inspect candidates).
6. THE System SHALL render Employee management pages: list (table with availability badge, workload indicator), detail/edit (profile form, skills editor, schedule editor).
7. THE System SHALL render Service Domain management pages: domain list table, domain create/edit form, predefined issues sub-table per domain with inline add/edit/delete.
8. THE System SHALL render User management pages: user list with role badge, create user form (role, org auto-assigned), activate/deactivate/reset-password actions.

---

### Requirement 17 — Testing

**User Story:** As a developer, I want a comprehensive test suite that guards correctness of authentication, authorization, data isolation, the assignment engine, and feedback flow.

#### Acceptance Criteria

1. THE System SHALL maintain all 47 existing backend tests passing without modification after Phase 3 changes.
2. THE System SHALL add tests for JWT login success and failure (invalid credentials, inactive account).
3. THE System SHALL add tests verifying that ADMIN and EMPLOYEE roles cannot be self-registered via the public register endpoint.
4. THE System SHALL add tests verifying that org-isolation is enforced: a user in org A cannot read, update, or delete a resource belonging to org B.
5. THE System SHALL add tests for ServiceRequest creation: valid submission creates request and triggers assignment, missing domain returns 400, empty description with no predefined issue returns 400.
6. THE System SHALL add tests for all ServiceRequest status transitions: CREATED → ASSIGNED, ASSIGNED → IN_PROGRESS, IN_PROGRESS → COMPLETED, COMPLETED → REOPENED, any status → CANCELLED.
7. THE System SHALL add tests for the AssignmentEngine eligibility filter: unavailable employee excluded, wrong-org employee excluded, at-capacity employee excluded, domain-mismatch employee excluded.
8. THE System SHALL add tests for distance-based ranking: the closer and higher-proficiency employee receives a higher suitability score.
9. THE System SHALL add tests for Feedback creation: rating persisted, resolution time calculated, `met_sla` derived correctly, unresolved feedback triggers reassignment.
10. THE System SHALL add tests for ServiceDomain CRUD: admin can create/update/delete within their org; employee and resident cannot create/update/delete.
11. THE System SHALL pass `python manage.py check --database default` with no errors.
12. THE System SHALL pass `python manage.py makemigrations --check` with no new migrations required.
13. THE System SHALL pass `npm run build` in the `frontend/` directory with no TypeScript or build errors.

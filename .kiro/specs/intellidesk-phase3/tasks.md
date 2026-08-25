# Implementation Plan: IntelliDesk Phase 3

## Overview

IntelliDesk Phase 3 is a production-ready build of an intelligent workforce helpdesk SaaS platform. This task plan breaks the implementation into five parallel-executable phases: (A) Authentication fixes and seed command, (B) Design system foundation, (C) Request wizard and domain forms, (D) Portal redesigns, and (E) API integration and testing.

All tasks are atomic and can be executed in order or in parallel within each phase. Each task includes references to specific requirements for traceability.

---

## Phase A: Authentication & Seed Command

- [x] 1. Fix AuthContext authentication flow
  - [x] 1.1 Fix AuthContext initialization sequence
    - Reorder initialization to token → me → organizations (prevent 401s)
    - Remove switchDemoRole function entirely
    - Guard apiOrganizations.list() behind successful user authentication
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [x] 1.2 Fix Navbar component
    - Remove role quick switcher bar and UI
    - Remove switchDemoRole function calls
    - Fix missing ZapIcon import from lucide-react
    - _Requirements: 2.1, 2.2, 2.5_

  - [x] 1.3 Fix AuthModal component
    - Remove role selector from registration form
    - Ensure all self-registrations create users with role='USER'
    - _Requirements: 2.3_

- [x] 2. Create idempotent seed_demo_data management command
  - [x] 2.1 Create Django management command structure
    - Create apps/accounts/management/commands/seed_demo_data.py
    - Implement handle() method with error handling
    - _Requirements: 3.1, 3.2_

  - [x] 2.2 Seed organizations, users, and admins
    - Create three organizations using get_or_create: Green Valley Residency (GATED_COMMUNITY), Sunrise Colony (RESIDENTIAL_COLONY), TechPark Business Center (OFFICE_SPACE)
    - Create superadmin, org admins, employees, and residents using get_or_create by username
    - Include realistic contact info and addresses for each organization
    - _Requirements: 3.1, 3.2_

  - [x] 2.3 Seed service domains and predefined issues
    - Create service domains (Electrical, Plumbing, HVAC, Cleaning, Carpentry, Security, IT Support, General Maintenance) for each organization
    - Create 5–7 predefined issues per domain using get_or_create
    - Set realistic SLA hours per domain
    - _Requirements: 3.4, 3.5_

  - [x] 2.4 Seed employee profiles with skills and schedules
    - Create 15 employee profiles across three organizations
    - Assign realistic skills to employees by domain expertise
    - Create EmployeeSchedule entries with realistic shift times
    - Assign realistic lat/lng locations for each employee
    - _Requirements: 3.3_

  - [x] 2.5 Seed historical completed requests with feedback
    - Create 15 completed ServiceRequest records with realistic timestamps (past 30 days)
    - For each completed request: create associated Feedback with rating (3–5), is_resolved status, and SLA met/missed mix
    - Create 5 active or in-progress requests
    - Create 3 urgent priority requests
    - _Requirements: 3.6, 3.7_

  - [x] 2.6 Verify idempotency
    - Run seed_demo_data twice in succession
    - Verify no duplicate organizations, users, employees, domains, issues, or requests created
    - Verify database state is identical on second run
    - _Requirements: 3.8, 3.9_

---

## Phase B: Design System & Application Foundation

- [x] 3. Add ServiceRequest.details_snapshot JSONField
  - [x] 3.1 Create Django migration
    - Add details_snapshot JSONField to ServiceRequest model with default=dict, blank=True
    - _Requirements: 6.15_

  - [x] 3.2 Apply and verify migration
    - Run python manage.py migrate
    - Verify schema change applied correctly
    - _Requirements: 6.15_

- [x] 4. Add PlatformAnalyticsView and fix AnalyticsService N+1
  - [x] 4.1 Create GET /api/analytics/platform/ endpoint
    - Add PlatformAnalyticsView for superusers only (IsAuthenticated + IsSuperuser check)
    - Return platform-wide KPIs: total organizations, total users, total employees, total requests, completion rate, average resolution time, overall satisfaction
    - _Requirements: 5.5, 5.6_

  - [x] 4.2 Refactor AnalyticsService.get_charts_data
    - Replace Python loop for feedback stats with single aggregated Django query
    - Use Avg() annotation for employee feedback averages
    - Eliminate N+1 queries
    - _Requirements: 11.1_

  - [x] 4.3 Test endpoint efficiency
    - Verify analytics endpoint returns data within <500ms
    - Verify no N+1 queries via Django Debug Toolbar or test assertions
    - _Requirements: 11.1_

- [x] 5. Design system: globals.css with color palette and typography
  - [x] 5.1 Update frontend/app/globals.css
    - Import Inter font from Google Fonts
    - Define CSS custom properties: --color-primary, --color-bg, --color-surface, --color-border, --color-text-primary, --color-text-muted, --color-success, --color-warning, --color-danger
    - Define domain color map: --color-electrical, --color-plumbing, --color-hvac, --color-cleaning, --color-carpentry, --color-security, --color-it-support, --color-general
    - Override Bootstrap variables (--bs-primary, --bs-secondary, etc.)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 5.2 Create domain color palette utilities
    - Create frontend/lib/colors.ts with domainColorMap function
    - _Requirements: 4.2_

  - [x] 5.3 Verify styles apply across components
    - Verify Inter font displays globally
    - Verify color variables propagate to Bootstrap components
    - Test across Firefox, Chrome, Safari
    - _Requirements: 4.1, 4.2, 4.5_

---

## Phase C: Request Wizard & Domain Forms

- [x] 6. Create Request Wizard main component and navigation
  - [x] 6.1 Create RequestWizard.tsx main component
    - Implement 6-step wizard state management (currentStep, formData, errors)
    - Add next/previous/submit handlers
    - Render appropriate WizardStep based on currentStep
    - _Requirements: 6.1_

  - [x] 6.2 Create WizardStep.tsx base component
    - Wrapper component for each wizard step with header, body, and navigation buttons
    - _Requirements: 6.1_

  - [x] 6.3 Create progress indicator component
    - Visual progress bar showing current step (1–6) with checkmarks for completed steps
    - _Requirements: 6.1_

- [x] 7. Implement Request Wizard Step 1: Service Domain Selection
  - [x] 7.1 Create steps/ServiceStep.tsx
    - Fetch active domains from GET /api/services/domains/ filtered by authenticated user's organization
    - Display domains as clickable cards with icons and descriptions
    - Allow domain selection and validation
    - _Requirements: 6.2_

- [x] 8. Implement Request Wizard Step 2: Problem Selection
  - [x] 8.1 Create steps/ProblemStep.tsx
    - Fetch predefined issues for selected domain from GET /api/services/issues/?domain={id}
    - Display issues as list or cards
    - Add "Other / Custom Issue" option at bottom
    - Allow issue selection
    - _Requirements: 6.3_

- [ ] 9. Implement Request Wizard Step 3: Domain-Specific Details
  - [x] 9.1 Create frontend/lib/domainForms.ts
    - Define field definitions for all 8 domain types (Electrical, Plumbing, HVAC, Cleaning, Carpentry, Security, IT Support, General Maintenance)
    - Each domain includes field name, label, type (text/number/boolean/textarea/select), and validation rules
    - _Requirements: 6.4–6.11_

  - [x] 9.2 Create DynamicForm.tsx component
    - Render form fields dynamically based on domainFieldDefinitions
    - Handle form data updates and validation
    - _Requirements: 6.14_

  - [ ] 9.3 Create domain-specific form components
    - [ ] 9.3a ElectricalForm.tsx: affected_equipment, affected_room, power_available, burning_smell, sparks, when_started, safety_concern, description
      - _Requirements: 6.4_
    
    - [ ] 9.3b PlumbingForm.tsx: fixture, severity, water_flowing, water_supply_affected, affected_room, when_started, description
      - _Requirements: 6.5_
    
    - [ ] 9.3c HVACForm.tsx: ac_type, room, cooling_severity, leakage, noise, smell, when_started, description
      - _Requirements: 6.6_
    
    - [ ] 9.3d CleaningForm.tsx: area_type, approximate_size, cleaning_type, preferred_time, special_requirements, description
      - _Requirements: 6.7_
    
    - [ ] 9.3e CarpentryForm.tsx: furniture_item, damage_problem, material, severity, location_detail, description
      - _Requirements: 6.8_
    
    - [ ] 9.3f SecurityForm.tsx: incident_type, location_detail, incident_time, safety_concern, description
      - _Requirements: 6.9_
    
    - [ ] 9.3g ITSupportForm.tsx: device, os, hardware_or_software, problem_type, error_description, when_started, location_detail, description
      - _Requirements: 6.10_
    
    - [ ] 9.3h GeneralMaintenanceForm.tsx: asset_item, problem_category, location_detail, when_started, description
      - _Requirements: 6.11_

  - [x] 9.4 Serialize form data to JSON
    - Implement serialization logic to convert Step 3 form data to JSON string for custom_description field
    - Also populate details_snapshot with same structured data
    - _Requirements: 6.14_

- [x] 10. Implement Request Wizard Step 4: Location Selection
  - [x] 10.1 Create steps/LocationStep.tsx
    - Determine organization type (GATED_COMMUNITY, RESIDENTIAL_COLONY, OFFICE_SPACE)
    - Show org-type-specific location fields:
      - GATED_COMMUNITY / RESIDENTIAL_COLONY: Tower, Floor, Flat Number, Room
      - OFFICE_SPACE: Building, Floor, Department, Room
    - Capture location data into form state
    - _Requirements: 6.12, 6.13_

- [x] 11. Implement Request Wizard Step 5: Priority Selection
  - [x] 11.1 Create steps/PriorityStep.tsx
    - Display visual priority selector with 5 options: Low, Normal, High, Urgent, Critical
    - Use color-coded badges (Low: green, Normal: blue, High: yellow, Urgent: orange, Critical: red)
    - Allow priority selection and store in form state
    - _Requirements: 6.5 (implied from design)_

- [x] 12. Implement Request Wizard Step 6: Review & Submit
  - [x] 12.1 Create steps/ReviewStep.tsx
    - Display summary of all previous steps (domain, issue, domain-specific details, location, priority)
    - Format details based on domain type for readability
    - Show edit buttons to go back to specific steps
    - _Requirements: 6.14_

  - [x] 12.2 Implement submission logic
    - On submit: call POST /api/requests/ with serialized form data
    - Pass custom_description (JSON string) and details_snapshot (JSON object)
    - Handle success: show success toast, close wizard, redirect to request detail or dashboard
    - Handle errors: display error message, allow retry
    - _Requirements: 6.14_

  - [x] 12.3 Handle error states
    - Display validation errors returned from backend
    - Show network error messages with retry option
    - _Requirements: 6.14_

---

## Phase D: Portal Redesigns (Parallel)

### Resident Portal

- [x] 13. Build Resident Portal
  - [x] 13.1 Create ResidentPortal.tsx layout
    - Centered card-based layout (no sidebar)
    - Header with greeting and New Request button
    - Request list section
    - Empty state placeholder
    - _Requirements: 7.1, 7.2, 7.5_

  - [x] 13.2 Implement request list with domain-colored cards
    - Fetch resident's requests from GET /api/requests/
    - Display each request as a card with: domain badge (colored by domain), issue title, priority badge, location, status badge, assigned employee name/phone, distance, SLA countdown
    - Cards should be clickable to view full request detail
    - _Requirements: 7.1_

  - [x] 13.3 Implement New Request button
    - Button launches RequestWizard component in full-screen modal or overlay
    - After wizard submission, refresh request list
    - _Requirements: 7.2_

  - [x] 13.4 Implement request detail view
    - Display on click of request card
    - Show: complete status timeline, employee contact information, domain-specific details (parsed from details_snapshot), status transitions with timestamps
    - _Requirements: 7.3_

  - [x] 13.5 Integrate feedback form
    - Show feedback form only if request status is COMPLETED
    - Form captures: is_resolved (boolean), rating (1–5 stars), comments
    - Submit to POST /api/feedback/
    - _Requirements: 7.4_

  - [x] 13.6 Implement empty state
    - Display when resident has no requests
    - Show illustration/icon and prompt to create first request
    - _Requirements: 7.5_

  - [x] 13.7 Fetch from real API only
    - Verify GET /api/requests/ is the only data source
    - No mock data in production code paths
    - _Requirements: 7.6, 10.1_

### Employee Portal

- [ ] 14. Build Employee Portal
  - [ ] 14.1 Create EmployeePortal.tsx with sidebar navigation
    - Sidebar with sections: Dashboard, My Tasks, History, Profile
    - Main content area renders section based on selected nav item
    - _Requirements: 8.1_

  - [ ] 14.2 Implement Dashboard with active assignments
    - Fetch active assignments from GET /api/assignments/?status=assigned or similar endpoint
    - Display as cards showing: priority badge (color-coded), location, resident contact info, distance, SLA countdown
    - Cards should highlight urgent assignments visually distinct
    - _Requirements: 8.2, 8.3_

  - [ ] 14.3 Implement Start Work / Complete Work buttons
    - "Start Work" button calls POST /api/requests/{id}/start_work/
    - "Complete Work" button calls POST /api/requests/{id}/complete_work/
    - Update card state after successful API call
    - _Requirements: 8.6, 8.7_

  - [ ] 14.4 Implement History page
    - Display completed assignments in a table with columns: issue title, resident name, priority, completed date, resident rating
    - Fetch from GET /api/requests/?status=completed or similar
    - _Requirements: 8.4_

  - [ ] 14.5 Implement Profile page
    - Display employee's skills (list or tags)
    - Display schedule (shift times and days)
    - Display cumulative performance stats: total assignments, completion rate, average rating, availability status
    - Fetch from GET /api/employees/me/
    - _Requirements: 8.5_

  - [ ] 14.6 Fetch from real API only
    - Verify no mock data in production code paths
    - All data from real API endpoints
    - _Requirements: 8.8, 10.1_

### Admin Portal

- [ ] 15. Build Admin Portal
  - [ ] 15.1 Create AdminPortal.tsx with sidebar navigation
    - Sidebar sections: Dashboard, Requests, Workforce, Services, Users, Reports
    - Main content area renders selected section
    - _Requirements: 9.1_

  - [ ] 15.2 Implement Admin Dashboard with KPI cards
    - Display KPI cards: total requests, open requests, in-progress requests, completed requests, urgent requests, SLA compliance rate, average rating, available employees count
    - Fetch from GET /api/analytics/overview/ (org-scoped)
    - Cards show key metric + trend indicator
    - _Requirements: 9.2_

  - [ ] 15.3 Implement Requests page with table
    - Display sortable, filterable, searchable table with columns: domain, issue title, resident name, priority badge, status badge, assigned employee, created date, SLA countdown
    - Implement search filter for issue/resident name
    - Implement status filter dropdown (CREATED, ASSIGNED, IN_PROGRESS, COMPLETED, PAUSED)
    - Implement priority filter dropdown
    - Implement sorting by date/status/priority
    - Fetch from GET /api/requests/?organization={org_id}
    - _Requirements: 9.3_

  - [ ] 15.4 Implement Workforce page with employee cards
    - Display cards for each organization employee showing: availability status (ON_DUTY, ON_LEAVE, OFF_DUTY), current workload (e.g., 3/5 assignments), skills list, quick-toggle button for availability
    - Implement click on toggle to call POST /api/employees/{id}/toggle_availability/
    - Fetch from GET /api/employees/
    - _Requirements: 9.4_

  - [ ] 15.5 Implement Services page with CRUD operations
    - Display service domains in a table or card list
    - For each domain: show name, SLA hours, is_active toggle
    - Implement "Create Domain" button → form modal
    - Implement "Edit" button → edit form modal
    - Implement "Delete" button → confirm and delete
    - Create/update/delete via POST/PATCH/DELETE /api/services/domains/
    - Display predefined issues for each domain (expandable)
    - Implement create/edit/delete for predefined issues under each domain
    - _Requirements: 9.5_

  - [ ] 15.6 Implement Users page for user management
    - Display table of organization users with columns: name, email, role, is_active status
    - Implement "Create User" button → form modal
    - Implement "Edit" button → edit form modal
    - Implement "Deactivate" button → confirm and deactivate
    - Create/update/deactivate via POST/PATCH /api/auth/users/
    - _Requirements: 9.6_

  - [ ] 15.7 Implement Reports page with analytics charts
    - Display chart 1: Request distribution by domain (bar or pie chart)
    - Display chart 2: Request priority distribution (bar or pie chart)
    - Display chart 3: Daily request trend over past 14 days (line chart)
    - Fetch from GET /api/analytics/charts/
    - _Requirements: 9.7_

  - [ ] 15.8 Fetch from real API only
    - Verify all data from real API endpoints
    - No mock data in production code paths
    - _Requirements: 9.8, 10.1_

### Super Admin Portal

- [ ] 16. Build Super Admin Portal
  - [ ] 16.1 Create SuperAdminPortal.tsx layout
    - Sidebar navigation (similar to Admin Portal)
    - Dashboard, Organizations, Users, Analytics sections
    - _Requirements: 5.1_

  - [ ] 16.2 Implement Dashboard with platform KPIs
    - Display KPI cards: total organizations, active organizations, total users, total employees, total requests, completion rate, average resolution time, overall satisfaction rating
    - Fetch from GET /api/analytics/platform/ (superuser only)
    - _Requirements: 5.1_

  - [ ] 16.3 Implement Organizations page with management table
    - Display table: name, type, user count, employee count, active request count, status, action buttons
    - Columns should include org status (ACTIVE, INACTIVE)
    - Action buttons: view details, edit, activate/deactivate
    - Fetch from GET /api/organizations/
    - _Requirements: 5.2_

  - [ ] 16.4 Implement Users page with search/filter
    - Display all platform users with search and filter
    - Filter by: organization (dropdown), role (dropdown), is_active (toggle)
    - Display table: name, email, organization, role, is_active status
    - Fetch from GET /api/auth/users/ with filters
    - _Requirements: 5.3, 5.7_

  - [ ] 16.5 Implement Analytics page with charts
    - Display chart 1: Total requests across all organizations (bar or line chart by organization)
    - Display chart 2: Requests by domain (bar or pie chart)
    - Display chart 3: Request status distribution (pie chart: CREATED, ASSIGNED, IN_PROGRESS, COMPLETED)
    - Fetch from GET /api/analytics/platform/
    - _Requirements: 5.4_

---

## Phase E: API Integration, Performance, Tests

- [ ] 17. Create shared UI components
  - [ ] 17.1 Create Sidebar.tsx component
    - Reusable sidebar navigation for Admin/Employee portals
    - Props: sections (array of nav items), onSelect callback
    - _Requirements: 2.5_

  - [ ] 17.2 Create KPICard.tsx component
    - Reusable KPI card showing metric, value, and optional trend indicator
    - Props: label, value, icon, trend (optional), color
    - _Requirements: 9.2, 5.2_

  - [ ] 17.3 Create RequestCard.tsx component
    - Reusable request card showing domain badge, issue, priority, location, SLA countdown
    - Domain badge color-coded by domain
    - _Requirements: 7.1, 13.2_

  - [ ] 17.4 Create AssignmentCard.tsx component
    - Reusable assignment card for employee portal showing priority, location, resident contact, distance, SLA
    - _Requirements: 8.2, 14.2_

  - [ ] 17.5 Create SkeletonLoader.tsx component
    - Loading state component with skeleton placeholders
    - Animates similar to actual component shape
    - _Requirements: 10.4_

  - [ ] 17.6 Create EmptyState.tsx component
    - Reusable empty state illustration component
    - Props: icon, title, description, action button (optional)
    - _Requirements: 7.5, 13.6_

- [ ] 18. Fix remaining API integration issues and optimize queries
  - [ ] 18.1 Audit all portal API calls
    - Review all GET/POST/PATCH/DELETE endpoints used by portals
    - Verify each endpoint is called with correct parameters and authentication
    - _Requirements: 10.1_

  - [ ] 18.2 Implement pagination for large datasets
    - Add pagination to GET /api/requests/, /api/assignments/, /api/employees/, /api/auth/users/
    - Frontend should handle paginated responses: { results: [], count: N, next: URL, previous: URL }
    - Implement next/previous page navigation in table/list components
    - _Requirements: 10.2_

  - [ ] 18.3 Add loading, error, and empty states
    - Every portal component fetching data should display:
      - Loading spinner/skeleton while fetching
      - Error message if fetch fails, with retry button
      - Empty state if no data matches filters
    - _Requirements: 10.3, 10.4_

  - [ ] 18.4 Fix N+1 queries in Django views
    - Review ServiceRequestViewSet to use select_related for organization, user, domain, predefined_issue
    - Review AssignmentViewSet to use select_related for request, employee, employee__user
    - Review EmployeeViewSet to use select_related for user, organization
    - Verify with Django Debug Toolbar or query counting tests
    - _Requirements: 11.2, 11.3_

  - [ ] 18.5 Prevent duplicate useEffect API calls
    - Review all React components using useEffect for data fetching
    - Ensure useEffect only runs once on mount (correct dependency array)
    - Verify no duplicate API calls in browser console Network tab
    - _Requirements: 11.4_

  - [ ] 18.6 Test all endpoints with real data
    - Test each portal's primary workflows with real API data
    - Verify no hardcoded mock data leaks into production components
    - _Requirements: 10.1_

- [ ] 19. Add animation system with GSAP
  - [ ] 19.1 Install GSAP
    - npm install gsap
    - _Requirements: (implied from design)_

  - [ ] 19.2 Implement page transition animations
    - Fade-in/slide-in animations when switching between portal sections
    - Duration: 300–400ms, easing: ease-out
    - _Requirements: (implied from design)_

  - [ ] 19.3 Implement card entrance animations
    - Staggered entrance for request/assignment cards when first loaded
    - Scale + fade-in from 0.9 to 1.0
    - Duration: 400ms, stagger: 50ms between cards
    - _Requirements: (implied from design)_

  - [ ] 19.4 Implement interactive micro-interactions
    - Sidebar hover effects (subtle color shift)
    - Button press animations (scale down on click)
    - Card hover lift effect (shadow increase)
    - Duration: 150–200ms
    - _Requirements: (implied from design)_

- [ ] 20. Backend test suite: Authentication, Authorization, Data Isolation
  - [ ] 20.1 Write AuthenticationTest class
    - Test login with valid credentials returns { access, refresh, user }
    - Test login with invalid credentials returns HTTP 401
    - Test GET /api/auth/me/ with valid token returns correct user profile
    - Test GET /api/auth/me/ with invalid token returns HTTP 401
    - Test token refresh flow
    - _Requirements: 12.1_

  - [ ] 20.2 Write AuthorizationTest class
    - Test Resident cannot access GET /api/analytics/overview/
    - Test Employee cannot access admin endpoints (Services, Users, Analytics)
    - Test Admin can access org-scoped endpoints
    - Test non-superuser cannot access GET /api/analytics/platform/
    - Test superuser can access GET /api/analytics/platform/
    - _Requirements: 12.2, 5.6_

  - [ ] 20.3 Write OrganizationIsolationTest class
    - Test user in Org A cannot read requests from Org B
    - Test user in Org A cannot read employees from Org B
    - Test user in Org A cannot access domains from Org B
    - Test user in Org A cannot submit feedback on requests from Org B
    - _Requirements: 12.3, 13.4_

- [ ] 21. Backend test suite: Business Logic
  - [ ] 21.1 Write ServiceRequestAPITest class
    - Test Resident can create request via POST /api/requests/
    - Test request creation with domain-specific details stores both custom_description and details_snapshot
    - Test request status transitions (CREATED → ASSIGNED → IN_PROGRESS → COMPLETED)
    - Test invalid status transitions return error
    - Test creating request triggers AssignmentService (assignment is created)
    - _Requirements: 12.4, 6.14, 14.2_

  - [ ] 21.2 Write FeedbackTest class
    - Test submitting feedback on COMPLETED request with is_resolved=False triggers request reopen
    - Test submitting feedback on COMPLETED request with is_resolved=True keeps status COMPLETED
    - Test resident can submit exactly one feedback per request (duplicate submission returns error)
    - Test feedback captures rating, is_resolved, comments correctly
    - _Requirements: 12.5_

  - [ ] 21.3 Write ServiceDomainCRUDTest class
    - Test Admin can create service domain via POST /api/services/domains/
    - Test Admin can update domain via PATCH /api/services/domains/{id}/
    - Test Admin can delete domain via DELETE /api/services/domains/{id}/
    - Test Admin can only see/modify domains in their organization
    - _Requirements: 12.6_

  - [ ] 21.4 Write SeedCommandTest class
    - Test seed_demo_data creates all 3 organizations
    - Test seed_demo_data creates users for each organization
    - Test seed_demo_data creates employees with skills and schedules
    - Test seed_demo_data creates service domains and predefined issues
    - Test seed_demo_data creates 15 historical requests + 5 active + 3 urgent
    - Test running seed_demo_data twice creates no duplicates (idempotency)
    - Test database state after 2 runs equals state after 1 run
    - _Requirements: 12.7, 3.8, 3.9_

- [ ] 22. Verify database and migrations
  - [ ] 22.1 Run Django system check
    - python manage.py check --database default
    - Verify zero errors/warnings
    - _Requirements: 12.8_

  - [ ] 22.2 Check for pending migrations
    - python manage.py makemigrations --check
    - Verify no pending migrations
    - _Requirements: 12.9_

  - [ ] 22.3 Verify database schema
    - Verify ServiceRequest.details_snapshot field exists in database
    - Verify all relationships (ForeignKeys, ManyToMany) are intact
    - Run python manage.py sqlmigrate to inspect migration SQL
    - _Requirements: 6.15_

- [ ] 23. Run full backend test suite
  - [ ] 23.1 Run all tests
    - python manage.py test --noinput
    - Capture output and verify all tests pass
    - _Requirements: 12.10_

  - [ ] 23.2 Count test results
    - Verify 47+ tests pass (47 from Phase 2 + new Phase 3 tests)
    - Fix any failures before proceeding
    - _Requirements: 12.10_

  - [ ] 23.3 Test coverage check (optional)
    - Verify critical paths (auth, assignment, isolation) have >80% coverage
    - _Requirements: 12.10_

- [ ] 24. Frontend build verification
  - [ ] 24.1 Run npm run build
    - npm run build in frontend directory
    - Capture output and check for errors
    - _Requirements: 12.11_

  - [ ] 24.2 Verify TypeScript errors
    - Verify zero TypeScript errors (no "error TS" messages)
    - _Requirements: 12.11_

  - [ ] 24.3 Verify bundle size
    - Check bundle size is reasonable (<500KB gzipped)
    - No unexpected large dependencies
    - _Requirements: 12.11_

- [ ] 25. Integration testing and bug fixes
  - [ ] 25.1 End-to-end workflow: Resident creates request
    - Login as resident
    - Click "New Request" → RequestWizard opens
    - Step 1: Select domain (e.g., Electrical)
    - Step 2: Select predefined issue
    - Step 3: Fill electrical-specific details
    - Step 4: Enter location (tower, floor, flat)
    - Step 5: Select priority
    - Step 6: Review and submit
    - Verify POST /api/requests/ called with correct data
    - Verify request appears in Resident Dashboard
    - _Requirements: 6.1–6.14, 7.1, 7.2_

  - [ ] 25.2 End-to-end workflow: Auto-assignment and employee work
    - Verify request creation triggers AssignmentService
    - Employee should see assignment in Employee Portal Dashboard
    - Employee clicks "Start Work" → request status becomes IN_PROGRESS
    - Employee clicks "Complete Work" → request status becomes COMPLETED
    - Request moves to Employee History with resident rating prompt
    - _Requirements: 8.1–8.7, 14.1–14.5_

  - [ ] 25.3 End-to-end workflow: Resident feedback and reopen
    - Resident views completed request in Resident Dashboard
    - Resident submits feedback with is_resolved=False
    - Request status reopens to IN_PROGRESS (or appropriate status)
    - Verify POST /api/feedback/ called and request reopened
    - _Requirements: 7.3, 7.4_

  - [ ] 25.4 Test Admin Portal workflows
    - Login as admin
    - Verify Dashboard shows KPIs from real API
    - Verify Requests page shows organization's requests
    - Verify Workforce page shows employees with workload
    - Verify Services page allows domain CRUD
    - Verify Users page shows organization users
    - Verify Reports page shows charts with real data
    - _Requirements: 9.1–9.8_

  - [ ] 25.5 Test Super Admin Portal workflows
    - Login as superuser
    - Verify Dashboard shows platform KPIs
    - Verify Organizations page lists all organizations
    - Verify Users page shows all users with org/role/status filters
    - Verify Analytics page shows platform-wide charts
    - _Requirements: 5.1–5.5_

  - [ ] 25.6 Test Request Wizard for each domain type
    - Create requests for Electrical, Plumbing, HVAC, Cleaning, Carpentry, Security, IT Support, General Maintenance
    - Verify domain-specific form fields appear correctly
    - Verify submitted data is captured in details_snapshot
    - _Requirements: 6.4–6.11_

  - [ ] 25.7 Test SLA countdown accuracy
    - Create request with domain SLA = 24 hours
    - Verify SLA countdown displays correct time remaining
    - Verify countdown updates in real-time
    - _Requirements: 7.1, 8.2_

  - [ ] 25.8 Test emergency reassignment flow
    - Admin reassigns an assignment (if endpoint exists)
    - Verify assignment changes to new employee
    - Verify old employee no longer sees assignment
    - Verify new employee sees assignment immediately
    - _Requirements: (implied from design)_

  - [ ] 25.9 Fix any failures
    - Document any bugs or issues found
    - Create bugfix commits for each issue
    - Retest after fixes
    - _Requirements: 12.10, 12.11_

---

## Checkpoint Tasks

- [ ] 26. Checkpoint: Phase A Complete
  - Authentication flow working without 401 errors
  - Demo UI removed (no role switcher, no debug tools)
  - Seed command creates idempotent data
  - Ask the user if questions arise before proceeding to Phase B

- [ ] 27. Checkpoint: Design System Complete
  - globals.css colors applied to all components
  - Inter font displays globally
  - Bootstrap variables overridden with design palette
  - Ask the user if questions arise before proceeding to Phase C

- [ ] 28. Checkpoint: Request Wizard Complete
  - All 6 steps render correctly
  - Domain-specific forms show/hide based on selection
  - Form data serializes correctly to JSON
  - Submission creates request with details_snapshot
  - Ask the user if questions arise before proceeding to Phase D

- [ ] 29. Checkpoint: All Portals Complete
  - Resident, Employee, Admin, Super Admin portals render
  - Each portal fetches from real API
  - No hardcoded mock data in production
  - Loading/error/empty states display correctly
  - Ask the user if questions arise before proceeding to Phase E

- [ ] 30. Final Checkpoint: All Tests Passing
  - Backend: python manage.py test --noinput passes with 47+ tests
  - Backend: python manage.py check --database default passes
  - Backend: python manage.py makemigrations --check shows no pending migrations
  - Frontend: npm run build completes with zero errors
  - All integration tests pass
  - All portals render correctly with real data
  - Seed command idempotency verified
  - Ask the user if questions arise before marking Phase 3 complete

---

## Notes

- Tasks marked with `*` are optional testing/refactoring tasks
- Each task references specific requirements for traceability
- Tasks within a phase can be executed in parallel; across phases, follow the sequence
- All API endpoints assume real data; no mock data should appear in production code
- Animation tasks (Task 19) are nice-to-have but can be deferred for MVP
- Database migrations must be created and applied before any feature code uses the new fields
- All Django tests must pass before frontend testing begins
- All frontend TypeScript must compile cleanly before integration testing begins


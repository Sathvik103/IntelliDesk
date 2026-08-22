from typing import List, Optional
from django.utils import timezone
from apps.employees.models import Employee, EmployeeSkill, EmployeeSchedule
from apps.requests.models import ServiceRequest

class CandidateSelector:
    """
    Stage 1: Hard Business Rules & Eligibility Filtering
    
    Filters out any employee that does not meet strict eligibility rules before
    features are extracted or ranking algorithms are invoked.
    
    Hard Rules Enforced:
    1. Tenant Isolation: Employee must belong to the exact same organization.
    2. Skill/Domain Requirement: Employee must have a registered EmployeeSkill in the requested domain.
    3. Status Check: Employee status must be ACTIVE (not ON_LEAVE, OFF_DUTY, or INACTIVE).
    4. Availability Toggle: Employee must have is_available=True.
    5. Workload Capacity: Employee active assignments count < max_active_assignments.
    6. Working Shift Schedule: If schedules exist, current day & time must fall within an active shift.
    7. Exclusion List: Supports excluding specific employee IDs (e.g., during reassignment).
    """

    @staticmethod
    def get_eligible_candidates(
        service_request: ServiceRequest,
        exclude_employee_ids: Optional[List[str]] = None,
        check_schedule: bool = True
    ) -> List[Employee]:
        org = service_request.organization
        domain = service_request.domain

        # 1. Base Query: Same organization, ACTIVE status, is_available=True
        queryset = Employee.objects.filter(
            organization=org,
            status=Employee.Status.ACTIVE,
            is_available=True
        ).select_related('user', 'role', 'organization').prefetch_related('skills__domain', 'schedules')

        if exclude_employee_ids:
            queryset = queryset.exclude(id__in=exclude_employee_ids)

        eligible_employees = []
        now = timezone.localtime(timezone.now()) if timezone.is_aware(timezone.now()) else timezone.now()
        current_day = now.weekday() # 0 = Monday, 6 = Sunday
        current_time = now.time()

        for employee in queryset:
            # 2. Skill/Domain Match Check
            has_domain_skill = any(skill.domain_id == domain.id for skill in employee.skills.all())
            if not has_domain_skill:
                continue

            # 3. Workload Capacity Check
            active_count = employee.assignments.filter(
                status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']
            ).count()
            if active_count >= employee.max_active_assignments:
                continue

            # 4. Schedule / Shift Check
            if check_schedule:
                emp_schedules = [s for s in employee.schedules.all() if s.is_active and s.day_of_week == current_day]
                if emp_schedules:
                    # If schedule configured for today, verify current time falls within at least one active slot
                    in_shift = any(s.start_time <= current_time <= s.end_time for s in emp_schedules)
                    if not in_shift:
                        continue

            eligible_employees.append(employee)

        return eligible_employees

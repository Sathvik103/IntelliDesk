from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q, F
from apps.requests.models import ServiceRequest
from apps.employees.models import Employee
from apps.services.models import ServiceDomain
from apps.feedback.models import Feedback
from apps.assignments.models import Assignment

class AnalyticsService:
    @staticmethod
    def get_platform_kpis():
        from apps.organizations.models import Organization
        from apps.accounts.models import User

        total_orgs = Organization.objects.count()
        active_orgs = Organization.objects.filter(is_active=True).count()
        total_users = User.objects.filter(is_superuser=False).count()
        total_employees = Employee.objects.count()
        total_requests = ServiceRequest.objects.count()
        completed_requests = ServiceRequest.objects.filter(status='COMPLETED').count()
        completion_rate = round((completed_requests / total_requests * 100), 1) if total_requests > 0 else 0.0

        avg_resolution = Feedback.objects.aggregate(avg=Avg('resolution_time_minutes'))['avg'] or 0.0
        avg_satisfaction = Feedback.objects.aggregate(avg=Avg('rating'))['avg'] or 0.0

        return {
            'total_organizations': total_orgs,
            'active_organizations': active_orgs,
            'total_users': total_users,
            'total_employees': total_employees,
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'completion_rate': completion_rate,
            'avg_resolution_time_mins': round(avg_resolution, 1),
            'overall_satisfaction': round(avg_satisfaction, 2),
        }


    @staticmethod
    def get_overview_kpis(organization=None, date_from=None, date_to=None):
        req_qs = ServiceRequest.objects.all()
        fb_qs = Feedback.objects.all()
        emp_qs = Employee.objects.all()

        if organization:
            req_qs = req_qs.filter(organization=organization)
            fb_qs = fb_qs.filter(request__organization=organization)
            emp_qs = emp_qs.filter(organization=organization)

        if date_from:
            req_qs = req_qs.filter(created_at__gte=date_from)
            fb_qs = fb_qs.filter(created_at__gte=date_from)
        if date_to:
            req_qs = req_qs.filter(created_at__lte=date_to)
            fb_qs = fb_qs.filter(created_at__lte=date_to)

        total_requests = req_qs.count()
        open_requests = req_qs.filter(status__in=['CREATED', 'QUEUED', 'ASSIGNED', 'IN_PROGRESS', 'REOPENED']).count()
        in_progress_requests = req_qs.filter(status='IN_PROGRESS').count()
        completed_requests = req_qs.filter(status='COMPLETED').count()
        urgent_requests = req_qs.filter(priority='URGENT').count()
        critical_requests = req_qs.filter(priority='CRITICAL').count()

        # Feedback stats
        fb_count = fb_qs.count()
        avg_rating = round(fb_qs.aggregate(avg=Avg('rating'))['avg'] or 5.0, 2)
        avg_resolution_mins = round(fb_qs.aggregate(avg=Avg('resolution_time_minutes'))['avg'] or 0.0, 1)

        met_sla_count = fb_qs.filter(met_sla=True).count()
        sla_compliance_rate = round((met_sla_count / fb_count * 100), 1) if fb_count > 0 else 100.0

        resolved_count = fb_qs.filter(is_resolved=True).count()
        resolution_rate = round((resolved_count / fb_count * 100), 1) if fb_count > 0 else (
            100.0 if completed_requests > 0 else 0.0
        )

        # Workforce stats
        total_employees = emp_qs.count()
        available_employees = emp_qs.filter(status='ACTIVE', is_available=True).count()
        unavailable_employees = emp_qs.filter(status='ACTIVE', is_available=False).count()

        # Employees at capacity: active_assignments >= max_active_assignments
        from apps.assignments.models import Assignment
        assign_qs = Assignment.objects.filter(
            status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']
        )
        if organization:
            assign_qs = assign_qs.filter(employee__organization=organization)

        from django.db.models import Count as DjCount
        employee_active_counts = assign_qs.values('employee_id').annotate(
            active=DjCount('id')
        )
        at_capacity_ids = set()
        for row in employee_active_counts:
            try:
                emp = emp_qs.get(id=row['employee_id'])
                if row['active'] >= emp.max_active_assignments:
                    at_capacity_ids.add(str(emp.id))
            except Exception:
                pass
        employees_at_capacity = len(at_capacity_ids)

        return {
            'total_requests': total_requests,
            'open_requests': open_requests,
            'in_progress_requests': in_progress_requests,
            'active_requests': in_progress_requests,
            'completed_requests': completed_requests,
            'urgent_requests': urgent_requests,
            'critical_requests': critical_requests,
            'avg_resolution_time_mins': avg_resolution_mins,
            'avg_rating': avg_rating,
            'sla_compliance_rate': sla_compliance_rate,
            'resolution_rate': resolution_rate,
            'total_employees': total_employees,
            'available_employees': available_employees,
            'unavailable_employees': unavailable_employees,
            'employees_at_capacity': employees_at_capacity,
        }


    @staticmethod
    def _employee_stats(emp, fb_by_emp, active_by_emp, completed_by_emp, total_by_emp):
        """Helper to extract employee statistics from aggregation results."""
        eid = str(emp.id)
        fb_data = fb_by_emp.get(eid, {})
        active_c = active_by_emp.get(eid, 0)
        completed_c = completed_by_emp.get(eid, 0)
        total_assigned = total_by_emp.get(eid, 0)

        total_fb = fb_data.get('total_fb', 0)
        met_sla_count = fb_data.get('met_sla_count', 0)

        completion_rate = round((completed_c / total_assigned * 100), 1) if total_assigned > 0 else 0.0
        sla_rate = round((met_sla_count / total_fb * 100), 1) if total_fb > 0 else 100.0

        return {
            'id': eid,
            'name': emp.user.get_full_name() or emp.user.username,
            'email': emp.user.email,
            'role': emp.role.title if emp.role else 'Technician',
            'status': emp.status,
            'is_available': emp.is_available,
            'current_active': active_c,
            'max_capacity': emp.max_active_assignments,
            'workload_pct': round((active_c / max(1, emp.max_active_assignments)) * 100, 1),
            'completed_total': completed_c,
            'completion_rate': completion_rate,
            'avg_rating': round(fb_data.get('avg_rating') or 5.0, 2),
            'avg_resolution_mins': round(fb_data.get('avg_resolution') or 0.0, 1),
            'sla_compliance_pct': sla_rate,
            'skills': [s.domain.name for s in emp.skills.all()],
        }

    @staticmethod
    def get_employee_scorecard(emp):
        """
        Returns the scorecard for a specific employee using the extracted helper.
        Returns the same structure as per-employee dict in workforce_performance.
        """
        from django.db.models import Avg as DjAvg, Count as DjCount2, Q
        from apps.feedback.models import Feedback as FB

        # Aggregate feedback for this employee
        emp_feedback = FB.objects.filter(employee=emp).aggregate(
            avg_rating=DjAvg('rating'),
            avg_resolution=DjAvg('resolution_time_minutes'),
            total_fb=DjCount2('id'),
            met_sla_count=DjCount2('id', filter=Q(met_sla=True)),
        )
        fb_by_emp = {str(emp.id): emp_feedback}

        # Aggregate active assignments
        active_assign = Assignment.objects.filter(
            employee=emp,
            status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']
        ).count()
        active_by_emp = {str(emp.id): active_assign}

        # Aggregate completed assignments
        completed_assign = Assignment.objects.filter(
            employee=emp,
            status='COMPLETED'
        ).count()
        completed_by_emp = {str(emp.id): completed_assign}

        # Total assignments
        total_assign = Assignment.objects.filter(employee=emp).count()
        total_by_emp = {str(emp.id): total_assign}

        return AnalyticsService._employee_stats(
            emp, fb_by_emp, active_by_emp, completed_by_emp, total_by_emp
        )

    @staticmethod
    def get_charts_data(organization=None, days: int = 14):
        req_qs = ServiceRequest.objects.all()
        fb_qs = Feedback.objects.all()
        emp_qs = Employee.objects.all()

        if organization:
            req_qs = req_qs.filter(organization=organization)
            fb_qs = fb_qs.filter(request__organization=organization)
            emp_qs = emp_qs.filter(organization=organization)

        # 1. Requests by Domain
        domain_counts = req_qs.values('domain__name').annotate(
            count=Count('id'),
            completed=Count('id', filter=Q(status='COMPLETED'))
        ).order_by('-count')

        by_domain = [
            {
                'domain': d['domain__name'] or 'Uncategorized',
                'count': d['count'],
                'completed': d['completed']
            }
            for d in domain_counts
        ]

        # 2. Requests by Priority
        priority_counts = req_qs.values('priority').annotate(count=Count('id')).order_by('priority')
        by_priority = [
            {'priority': p['priority'], 'count': p['count']}
            for p in priority_counts
        ]

        # 3. Requests by Status
        status_counts = req_qs.values('status').annotate(count=Count('id')).order_by('status')
        by_status = [
            {'status': s['status'], 'count': s['count']}
            for s in status_counts
        ]

        # 4. Volume Over Time (past N days)
        now = timezone.now()
        start_date = (now - timedelta(days=days)).date()
        daily_trend = []
        for i in range(days + 1):
            day_date = start_date + timedelta(days=i)
            day_start = timezone.make_aware(timezone.datetime.combine(day_date, timezone.datetime.min.time()))
            day_end = timezone.make_aware(timezone.datetime.combine(day_date, timezone.datetime.max.time()))
            
            created_c = req_qs.filter(created_at__range=(day_start, day_end)).count()
            completed_c = req_qs.filter(completed_at__range=(day_start, day_end)).count()
            daily_trend.append({
                'date': day_date.strftime('%b %d'),
                'created': created_c,
                'completed': completed_c
            })

        # 5. User Satisfaction Breakdown (1 to 5 Stars)
        ratings_dist = fb_qs.values('rating').annotate(count=Count('id')).order_by('rating')
        rating_map = {r['rating']: r['count'] for r in ratings_dist}
        satisfaction_breakdown = [
            {'stars': f"{s} Star", 'rating': s, 'count': rating_map.get(s, 0)}
            for s in range(1, 6)
        ]

        # 6. Employee Workload & Performance Table — aggregated, no N+1
        employees_summary = []
        emp_list = emp_qs.select_related('user', 'role').prefetch_related(
            'skills__domain',
            'assignments__request__feedback'
        )
        # Use annotation for feedback averages instead of Python loop
        from django.db.models import Avg as DjAvg, Count as DjCount2
        from apps.feedback.models import Feedback as FB

        emp_feedback_agg = FB.objects.filter(
            employee__in=emp_qs
        ).values('employee_id').annotate(
            avg_rating=DjAvg('rating'),
            avg_resolution=DjAvg('resolution_time_minutes'),
            total_fb=DjCount2('id'),
            met_sla_count=DjCount2('id', filter=Q(met_sla=True)),
        )
        fb_by_emp = {str(row['employee_id']): row for row in emp_feedback_agg}

        active_assign_agg = Assignment.objects.filter(
            employee__in=emp_qs,
            status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']
        ).values('employee_id').annotate(active=DjCount2('id'))
        active_by_emp = {str(row['employee_id']): row['active'] for row in active_assign_agg}

        completed_assign_agg = Assignment.objects.filter(
            employee__in=emp_qs,
            status='COMPLETED'
        ).values('employee_id').annotate(completed=DjCount2('id'))
        completed_by_emp = {str(row['employee_id']): row['completed'] for row in completed_assign_agg}

        total_assign_agg = Assignment.objects.filter(
            employee__in=emp_qs
        ).values('employee_id').annotate(total=DjCount2('id'))
        total_by_emp = {str(row['employee_id']): row['total'] for row in total_assign_agg}

        for emp in emp_list:
            stats_dict = AnalyticsService._employee_stats(
                emp, fb_by_emp, active_by_emp, completed_by_emp, total_by_emp
            )
            employees_summary.append(stats_dict)

        return {
            'by_domain': by_domain,
            'by_priority': by_priority,
            'by_status': by_status,
            'daily_trend': daily_trend,
            'satisfaction_breakdown': satisfaction_breakdown,
            'workforce_performance': employees_summary,
        }

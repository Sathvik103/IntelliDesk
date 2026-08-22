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

        # 6. Employee Workload & Performance Table
        employees_summary = []
        for emp in emp_qs.select_related('user', 'role').prefetch_related('skills__domain'):
            emp_assignments = emp.assignments.all()
            completed_c = emp_assignments.filter(status='COMPLETED').count()
            active_c = emp_assignments.filter(status__in=['ASSIGNED', 'ACCEPTED', 'IN_PROGRESS']).count()
            
            emp_feedbacks = [a.request.feedback for a in emp_assignments if hasattr(a.request, 'feedback')]
            if emp_feedbacks:
                emp_avg_rating = round(sum(f.rating for f in emp_feedbacks) / len(emp_feedbacks), 2)
                emp_sla_rate = round(sum(1 for f in emp_feedbacks if f.met_sla) / len(emp_feedbacks) * 100, 1)
                res_times = [f.resolution_time_minutes for f in emp_feedbacks if f.resolution_time_minutes > 0]
                emp_avg_time = round(sum(res_times) / len(res_times), 1) if res_times else 0.0
            else:
                emp_avg_rating = 5.0
                emp_sla_rate = 100.0
                emp_avg_time = 0.0

            total_assigned = emp_assignments.count()
            completion_rate = round((completed_c / total_assigned * 100), 1) if total_assigned > 0 else 0.0

            employees_summary.append({
                'id': str(emp.id),
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
                'avg_rating': emp_avg_rating,
                'avg_resolution_mins': emp_avg_time,
                'sla_compliance_pct': emp_sla_rate,
                'skills': [s.domain.name for s in emp.skills.all()],
            })

        return {
            'by_domain': by_domain,
            'by_priority': by_priority,
            'by_status': by_status,
            'daily_trend': daily_trend,
            'satisfaction_breakdown': satisfaction_breakdown,
            'workforce_performance': employees_summary,
        }

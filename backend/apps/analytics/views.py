from rest_framework import views, permissions
from rest_framework.response import Response
from .services import AnalyticsService
from apps.accounts.permissions import IsAdminRole, IsEmployeeRole

class AnalyticsOverviewView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Org-scoping: superusers see all-org data, others see only their org
        org = None if user.is_superuser else user.organization
        kpis = AnalyticsService.get_overview_kpis(organization=org)
        return Response(kpis)

class AnalyticsChartsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # Org-scoping: superusers see all-org data, others see only their org
        org = None if user.is_superuser else user.organization
        days = int(request.query_params.get('days', 14))
        charts = AnalyticsService.get_charts_data(organization=org, days=days)
        return Response(charts)

class PlatformAnalyticsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'Superuser access required.'}, status=403)
        data = AnalyticsService.get_platform_kpis()
        return Response(data)

class EmployeeScorecardView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        from apps.employees.models import Employee
        from django.shortcuts import get_object_or_404
        
        # Determine which employee to fetch
        if pk:
            employee = get_object_or_404(Employee, id=pk)
        else:
            # Look up the authenticated user's employee profile
            if not hasattr(request.user, 'employee_profile'):
                return Response({'error': 'Employee profile not found.'}, status=404)
            employee = request.user.employee_profile
        
        # Org isolation: ensure non-superusers can only view their org's employees
        if not request.user.is_superuser and employee.organization != request.user.organization:
            return Response({'error': 'Access denied.'}, status=403)
        
        # Return the employee scorecard
        scorecard = AnalyticsService.get_employee_scorecard(employee)
        return Response(scorecard)


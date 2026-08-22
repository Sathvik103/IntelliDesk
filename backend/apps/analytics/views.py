from rest_framework import views, permissions
from rest_framework.response import Response
from .services import AnalyticsService
from apps.accounts.permissions import IsAdminRole, IsEmployeeRole

class AnalyticsOverviewView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        org = None if user.is_superuser else user.organization
        kpis = AnalyticsService.get_overview_kpis(organization=org)
        return Response(kpis)

class AnalyticsChartsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        org = None if user.is_superuser else user.organization
        days = int(request.query_params.get('days', 14))
        charts = AnalyticsService.get_charts_data(organization=org, days=days)
        return Response(charts)

class EmployeeScorecardView(views.APIView):
    permission_classes = [IsEmployeeRole]

    def get(self, request, pk=None):
        # Allow viewing specific employee scorecard (for admin) or self
        employee_id = pk or getattr(getattr(request.user, 'employee_profile', None), 'id', None)
        if not employee_id:
            return Response({'error': 'Employee profile not found.'}, status=404)
        
        # Return specific employee metrics
        # For simplicity, return employee stats
        return Response({'employee_id': str(employee_id)})

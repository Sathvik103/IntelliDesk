from django.urls import path
from .views import AnalyticsOverviewView, AnalyticsChartsView, EmployeeScorecardView, PlatformAnalyticsView

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('charts/', AnalyticsChartsView.as_view(), name='analytics-charts'),
    path('platform/', PlatformAnalyticsView.as_view(), name='analytics-platform'),
    path('employee/<uuid:pk>/', EmployeeScorecardView.as_view(), name='employee-scorecard'),
]

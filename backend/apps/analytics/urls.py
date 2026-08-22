from django.urls import path
from .views import AnalyticsOverviewView, AnalyticsChartsView, EmployeeScorecardView

urlpatterns = [
    path('overview/', AnalyticsOverviewView.as_view(), name='analytics-overview'),
    path('charts/', AnalyticsChartsView.as_view(), name='analytics-charts'),
    path('employee/<uuid:pk>/', EmployeeScorecardView.as_view(), name='employee-scorecard'),
]

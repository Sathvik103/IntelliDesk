from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet,
    EmployeeRoleViewSet,
    EmployeeSkillViewSet,
    EmployeeScheduleViewSet,
)

router = DefaultRouter()
router.register(r'roles', EmployeeRoleViewSet, basename='employee-role')
router.register(r'skills', EmployeeSkillViewSet, basename='employee-skill')
router.register(r'schedules', EmployeeScheduleViewSet, basename='employee-schedule')
router.register(r'', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('', include(router.urls)),
]

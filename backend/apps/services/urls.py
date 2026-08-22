from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceDomainViewSet, PredefinedIssueViewSet

router = DefaultRouter()
router.register(r'domains', ServiceDomainViewSet, basename='domain')
router.register(r'issues', PredefinedIssueViewSet, basename='issue')

urlpatterns = [
    path('', include(router.urls)),
]

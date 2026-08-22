from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/services/', include('apps.services.urls')),
    path('api/employees/', include('apps.employees.urls')),
    path('api/requests/', include('apps.requests.urls')),
    path('api/assignments/', include('apps.assignments.urls')),
    path('api/feedback/', include('apps.feedback.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
]

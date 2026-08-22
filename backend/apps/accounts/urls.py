from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, RegisterView, CurrentUserView, UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('', include(router.urls)),
]

from rest_framework import status, views, permissions, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer
from .permissions import IsAdminRole


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class RegisterView(views.APIView):
    """
    Public self-registration. Restricted to USER (resident) role.
    ADMIN and EMPLOYEE accounts must be created by an admin via UserViewSet.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data.copy()
        # Prevent self-escalation to privileged roles
        if data.get('role') in ['ADMIN', 'EMPLOYEE']:
            return Response(
                {'error': 'Self-registration is only available for resident accounts. '
                          'Contact your administrator to create staff accounts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'User registered successfully.',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class CurrentUserView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    Admin user management. Scoped to the admin's organization.
    Superusers see all users.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['created_at', 'username', 'first_name']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all().select_related('organization')
        return User.objects.filter(
            organization=user.organization
        ).select_related('organization')

    def perform_create(self, serializer):
        """Auto-assign the requesting admin's organization when creating users."""
        if not self.request.user.is_superuser and self.request.user.organization:
            serializer.save(organization=self.request.user.organization)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account."""
        target = self.get_object()
        target.is_active = True
        target.save(update_fields=['is_active'])
        return Response({'status': 'activated', 'user_id': str(target.id)})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user account."""
        target = self.get_object()
        if target == request.user:
            return Response(
                {'error': 'You cannot deactivate your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        target.is_active = False
        target.save(update_fields=['is_active'])
        return Response({'status': 'deactivated', 'user_id': str(target.id)})

    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        """Admin reset of a user's password."""
        target = self.get_object()
        new_password = request.data.get('password', '').strip()
        if len(new_password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        target.set_password(new_password)
        target.save(update_fields=['password'])
        return Response({'status': 'password updated'})


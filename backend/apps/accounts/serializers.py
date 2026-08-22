from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from apps.organizations.serializers import OrganizationSerializer

class UserSerializer(serializers.ModelSerializer):
    organization_details = OrganizationSerializer(source='organization', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'organization',
            'organization_details',
            'phone',
            'address',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role',
            'organization',
            'phone',
            'address',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            # Also try email if username doesn't match
            try:
                user_obj = User.objects.get(email=username)
                if user_obj.check_password(password):
                    user = user_obj
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError("Invalid credentials provided.")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")

        refresh = RefreshToken.for_user(user)
        return {
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

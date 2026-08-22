from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser)
        )

class IsEmployeeRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['EMPLOYEE', 'ADMIN']
        )

class IsResidentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated
        )

class IsSameOrganization(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        user_org = getattr(request.user, 'organization_id', None)
        obj_org = getattr(obj, 'organization_id', None)
        if hasattr(obj, 'organization'):
            obj_org = obj.organization.id if obj.organization else None
        return user_org is not None and user_org == obj_org

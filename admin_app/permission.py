from rest_framework.permissions import BasePermission

from admin_app.models import AdminProfile


class IsSchoolAdmin(BasePermission):
    """
    Permission that checks if:
    1. User is authenticated
    2. User has an AdminProfile
    3. User's role is 'admin'
    4. (Optional) User belongs to the same school as the resource
    """

    def has_permission(self, request, view):
        # Authentication check
        if not request.user.is_authenticated:
            return False

        # Admin profile and role check
        try:
            if not hasattr(request.user, 'admin_profile'):
                return False

            if request.user.admin_profile.role != AdminProfile.Role.ADMIN:
                return False
        except Exception:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # Additional check for object-level permissions
        # Example: Verify user's school matches object's school
        if hasattr(obj, 'school'):
            return request.user.school == obj.school
        return True



def AnyOf(*perms):
    class _AnyOf(BasePermission):
        def has_permission(self, request, view):
            return any(perm().has_permission(request, view) for perm in perms)

        def has_object_permission(self, request, view, obj):
            return any(perm().has_object_permission(request, view, obj) for perm in perms if
                       hasattr(perm, 'has_object_permission'))

    return _AnyOf


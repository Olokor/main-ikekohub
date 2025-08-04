from rest_framework import permissions

from student_app.models import StudentProfile


class IsStudent(permissions.BasePermission):
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
            if not hasattr(request.user, 'student_profile'):
                return False

            if request.user.student_profile.role != StudentProfile.Role.STUDENT:
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
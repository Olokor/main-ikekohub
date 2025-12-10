from ikekohub.test import BaseTenantTestCase
from django_tenants.utils import tenant_context

from public_app.models import TenantUser
from teacher_app.models import TeacherProfile


class TeacherProfileModelTests(BaseTenantTestCase):
    """Tests for TeacherProfile model"""

    def test_create_teacher_profile_success(self):
        """Test successful teacher profile creation"""
        with tenant_context(self.tenant):
            user = TenantUser.objects.create_user(
                username='newteacher',
                email='newteacher@testschool.com',
                password='testpass123',
                school=self.school
            )

            profile = TeacherProfile.objects.create(
                user=user,
                class_level=self.class_level,
                subject_taught=['Science', 'Math']
            )

            self.assertEqual(profile.user, user)
            self.assertEqual(profile.class_level, self.class_level)
            self.assertEqual(profile.subject_taught, ['Science', 'Math'])
            self.assertEqual(profile.role, 'teacher')

    def test_teacher_profile_str_method(self):
        """Test string representation"""
        expected = f"{self.teacher_user.username} - teacher"
        self.assertEqual(str(self.teacher_profile), expected)

    def test_subject_taught_json_field(self):
        """Test JSON field for subjects taught"""
        with tenant_context(self.tenant):
            subjects = ['Math', 'Science', 'English']
            self.teacher_profile.subject_taught = subjects
            self.teacher_profile.save()

            # Refresh from database
            self.teacher_profile.refresh_from_db()
            self.assertEqual(self.teacher_profile.subject_taught, subjects)


class TeacherPermissionTests(BaseTenantTestCase):
    """Tests for teacher permissions"""

    def test_is_teacher_permission_valid_teacher(self):
        """Test permission for valid teacher"""
        from teacher_app.permission import IsTeacher
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.teacher_user

        permission = IsTeacher()
        self.assertTrue(permission.has_permission(request, None))

    def test_is_teacher_permission_invalid_user(self):
        """Test permission for non-teacher user"""
        from teacher_app.permission import IsTeacher
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.student_user  # Not a teacher

        permission = IsTeacher()
        self.assertFalse(permission.has_permission(request, None))


class TeacherViewTests(BaseTenantTestCase):
    """Tests for teacher views"""

    def test_teacher_dashboard_access_authorized(self):
        """Test teacher dashboard access for authorized teacher"""
        url = '/api-tenant/teacher/teacher-dashboard/'

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.teacher_user)
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['message'], 'Teacher Dashboard')

    def test_teacher_dashboard_access_unauthorized(self):
        """Test teacher dashboard access for unauthorized user"""
        url = '/api-tenant/teacher/teacher-dashboard/'

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.student_user)  # Not a teacher
            response = self.client.get(url)

            self.assertEqual(response.status_code, 403)


class StudentViewTests(BaseTenantTestCase):
    """Tests for student views"""

    def test_student_dashboard_access_authorized(self):
        """Test student dashboard access for authorized student"""
        url = '/api-tenant/student/student-dashboard/'

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.student_user)
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)

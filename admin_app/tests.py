from admin_app.models import AdminProfile
from ikekohub.test import BaseTenantTestCase
from django_tenants.utils import tenant_context

from public_app.models import TenantUser


class AdminProfileModelTests(BaseTenantTestCase):
    """Tests for AdminProfile model"""

    def test_create_admin_profile_success(self):
        """Test successful admin profile creation"""
        with tenant_context(self.tenant):
            user = TenantUser.objects.create_user(
                username='newadmin',
                email='newadmin@testschool.com',
                password='testpass123',
                school=self.school
            )

            profile = AdminProfile.objects.create(
                user=user,
                department='IT',
                role=AdminProfile.Role.ADMIN
            )

            self.assertEqual(profile.user, user)
            self.assertEqual(profile.department, 'IT')
            self.assertEqual(profile.role, 'admin')

    def test_admin_profile_str_method(self):
        """Test string representation"""
        self.assertEqual(str(self.admin_profile), 'admin')

    def test_role_choices(self):
        """Test role choices validation"""
        with tenant_context(self.tenant):
            self.admin_profile.role = 'teacher'
            self.admin_profile.save()
            self.assertEqual(self.admin_profile.role, 'teacher')

            # Test invalid role
            with self.assertRaises(Exception):
                self.admin_profile.role = 'invalid_role'
                self.admin_profile.full_clean()


class AdminPermissionTests(BaseTenantTestCase):
    """Tests for admin permissions"""

    def test_is_school_admin_permission_valid_admin(self):
        """Test permission for valid admin"""
        from admin_app.permission import IsSchoolAdmin
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.admin_user

        permission = IsSchoolAdmin()
        self.assertTrue(permission.has_permission(request, None))

    def test_is_school_admin_permission_invalid_user(self):
        """Test permission for non-admin user"""
        from admin_app.permission import IsSchoolAdmin
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.teacher_user  # Not an admin

        permission = IsSchoolAdmin()
        self.assertFalse(permission.has_permission(request, None))

    def test_is_school_admin_permission_unauthenticated(self):
        """Test permission for unauthenticated user"""
        from admin_app.permission import IsSchoolAdmin
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth.models import AnonymousUser

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = AnonymousUser()

        permission = IsSchoolAdmin()
        self.assertFalse(permission.has_permission(request, None))


class SignalsTests(BaseTenantTestCase):
    """Tests for Django signals"""

    def test_parent_creation_signal(self):
        """Test automatic parent creation when student is created"""
        with tenant_context(self.tenant):
            # Create new student user
            student_user = TenantUser.objects.create_user(
                username='newsignal_student',
                email='newsignal_student@testschool.com',
                password='testpass123',
                school=self.school
            )

            # Create student profile - should trigger parent creation
            student_profile = StudentProfile.objects.create(
                user=student_user,
                admission_number='STU003',
                date_of_birth='2018-01-01',
                parent_name='Signal Parent',
                parent_contact='1111111111',
                parent_email='signalparent@example.com',
                address='Signal Address',
                class_level=self.class_level,
                academic_year='2024-2025'
            )

            # Check if parent was created
            self.assertTrue(
                TenantUser.objects.filter(email='signalparent@example.com').exists()
            )

            parent_user = TenantUser.objects.get(email='signalparent@example.com')
            self.assertTrue(hasattr(parent_user, 'parent_profile'))

            # Check if child is linked to parent
            parent_profile = parent_user.parent_profile
            self.assertIn(student_profile, parent_profile.children.all())

    def test_user_deletion_on_student_deletion(self):
        """Test user deletion when student is deleted"""
        with tenant_context(self.tenant):
            user_id = self.student_profile.user.id

            # Delete student profile
            self.student_profile.delete()

            # User should also be deleted
            self.assertFalse(TenantUser.objects.filter(id=user_id).exists())


class AdminSerializerTests(BaseTenantTestCase):
    """Tests for admin serializers"""

    def test_admin_profile_serializer_valid_data(self):
        """Test AdminProfileSerializer with valid data"""
        from admin_app.serializer import AdminProfileSerializer

        data = {
            'username': 'newadmin',
            'email': 'newadmin@testschool.com',
            'password': 'newpass123',
            'school': 'Test School',
            'department': 'HR'
        }

        with tenant_context(self.tenant):
            serializer = AdminProfileSerializer(data=data)
            self.assertTrue(serializer.is_valid())

            admin_data = serializer.save()
            self.assertEqual(admin_data['username'], 'newadmin')
            self.assertEqual(admin_data['school'], 'Test School')

    def test_admin_profile_serializer_invalid_school(self):
        """Test AdminProfileSerializer with invalid school"""
        from admin_app.serializer import AdminProfileSerializer

        data = {
            'username': 'newadmin',
            'email': 'newadmin@testschool.com',
            'password': 'newpass123',
            'school': 'Nonexistent School',
            'department': 'HR'
        }

        with tenant_context(self.tenant):
            serializer = AdminProfileSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('school', serializer.errors)


class AdminViewTests(BaseTenantTestCase):
    """Tests for admin views"""

    def test_create_admin_user_view_success(self):
        """Test successful admin creation via API"""
        from rest_framework.test import force_authenticate
        from django.urls import reverse

        url = '/api-tenant/admin/create-admin/'
        data = {
            'username': 'apiadmin',
            'email': 'apiadmin@testschool.com',
            'password': 'apipass123',
            'school': 'Test School',
            'department': 'API Department'
        }

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.admin_user)
            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['username'], 'apiadmin')

    def test_create_admin_user_view_unauthorized(self):
        """Test admin creation with unauthorized user"""
        url = '/api-tenant/admin/create-admin/'
        data = {
            'username': 'unauthorizedadmin',
            'email': 'unauthorized@testschool.com',
            'password': 'pass123',
            'school': 'Test School',
            'department': 'Unauthorized'
        }

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.student_user)  # Not admin
            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, 403)

    def test_create_teacher_view_success(self):
        """Test successful teacher creation via API"""
        url = '/api-tenant/admin/create-teacher/'
        data = {
            'username': 'apiteacher',
            'email': 'apiteacher@testschool.com',
            'password': 'teacherpass123',
            'school': 'Test School'
        }

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.admin_user)
            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['username'], 'apiteacher')

    def test_create_student_view_success(self):
        """Test successful student creation via API"""
        url = '/api-tenant/admin/create-student/'
        data = {
            'username': 'apistudent',
            'first_name': 'API',
            'last_name': 'Student',
            'email': 'apistudent@testschool.com',
            'password': 'studentpass123',
            'school': 'Test School',
            'admission_number': 'STU005',
            'date_of_birth': '2018-05-20',
            'parent_name': 'API Parent',
            'parent_email': 'apiparent@example.com',
            'parent_contact': '9999999999',
            'address': 'API Address',
            'class_level': self.class_level.id,
            'academic_year': '2024-2025'
        }

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.admin_user)
            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['username'], 'apistudent')

    def test_bulk_student_creation_success(self):
        """Test bulk student creation"""
        url = '/api-tenant/admin/create-students/'
        data = [
            {
                'username': 'bulk1',
                'first_name': 'Bulk',
                'last_name': 'One',
                'email': 'bulk1@testschool.com',
                'password': 'bulkpass123',
                'school': 'Test School',
                'admission_number': 'BULK001',
                'date_of_birth': '2018-01-01',
                'parent_name': 'Bulk Parent 1',
                'parent_email': 'bulkparent1@example.com',
                'parent_contact': '1111111111',
                'address': 'Bulk Address 1',
                'class_level': self.class_level.id,
                'academic_year': '2024-2025'
            },
            {
                'username': 'bulk2',
                'first_name': 'Bulk',
                'last_name': 'Two',
                'email': 'bulk2@testschool.com',
                'password': 'bulkpass123',
                'school': 'Test School',
                'admission_number': 'BULK002',
                'date_of_birth': '2018-02-01',
                'parent_name': 'Bulk Parent 2',
                'parent_email': 'bulkparent2@example.com',
                'parent_contact': '2222222222',
                'address': 'Bulk Address 2',
                'class_level': self.class_level.id,
                'academic_year': '2024-2025'
            }
        ]

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.admin_user)
            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, 201)
            self.assertEqual(len(response.data['successfully_created']), 2)
            self.assertNotIn('errors', response.data)

    def test_bulk_student_creation_partial_failure(self):
        """Test bulk student creation with some failures"""
        url = '/api-tenant/admin/create-students/'
        data = [
            {
                'username': 'validbulk',
                'first_name': 'Valid',
                'last_name': 'Student',
                'email': 'validbulk@testschool.com',
                'password': 'validpass123',
                'school': 'Test School',
                'admission_number': 'VALID001',
                'date_of_birth': '2018-01-01',
                'parent_name': 'Valid Parent',
                'parent_email': 'validparent@example.com',
                'parent_contact': '3333333333',
                'address': 'Valid Address',
                'class_level': self.class_level.id,
                'academic_year': '2024-2025'
            },
            {
                'username': 'invalid',
                'email': 'invalid-email',  # Invalid email
                'password': 'pass',
                'school': 'Nonexistent School',  # Invalid school
                'admission_number': 'STU001',  # Duplicate admission number
                'date_of_birth': 'invalid-date'
            }
        ]

        with tenant_context(self.tenant):
            self.client.force_authenticate(user=self.admin_user)
            response = self.client.post(url, data, format='json')

            self.assertEqual(response.status_code, 207)  # Multi-status
            self.assertEqual(len(response.data['successfully_created']), 1)
            self.assertIn('errors', response.data)
            self.assertEqual(len(response.data['errors']), 1)
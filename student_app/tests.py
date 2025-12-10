from ikekohub.test import BaseTenantTestCase
from public_app.models import TenantUser
from django_tenants.utils import tenant_context

from student_app.models import StudentProfile


class StudentProfileModelTests(BaseTenantTestCase):
    """Tests for StudentProfile model"""

    def test_create_student_profile_success(self):
        """Test successful student profile creation"""
        with tenant_context(self.tenant):
            user = TenantUser.objects.create_user(
                username='newstudent',
                email='newstudent@testschool.com',
                password='testpass123',
                school=self.school
            )

            profile = StudentProfile.objects.create(
                user=user,
                admission_number='STU002',
                date_of_birth='2018-06-15',
                parent_name='Jane Doe',
                parent_contact='0987654321',
                parent_email='jane@example.com',
                address='456 Test Avenue',
                class_level=self.class_level,
                academic_year='2024-2025'
            )

            self.assertEqual(profile.admission_number, 'STU002')
            self.assertEqual(profile.parent_name, 'Jane Doe')
            self.assertEqual(profile.class_level, self.class_level)

    def test_admission_number_unique_constraint(self):
        """Test admission number uniqueness"""
        with tenant_context(self.tenant):
            user2 = TenantUser.objects.create_user(
                username='student2',
                email='student2@testschool.com',
                password='testpass123',
                school=self.school
            )

            with self.assertRaises(Exception):
                StudentProfile.objects.create(
                    user=user2,
                    admission_number='STU001',  # Already exists
                    date_of_birth='2018-06-15',
                    parent_name='Jane Doe',
                    parent_contact='0987654321',
                    parent_email='jane@example.com',
                    address='456 Test Avenue',
                    class_level=self.class_level,
                    academic_year='2024-2025'
                )

    def test_student_profile_str_method(self):
        """Test string representation"""
        expected = f"{self.student_user.username} student"
        self.assertEqual(str(self.student_profile), expected)


class StudentSerializerTests(BaseTenantTestCase):
    """Tests for student serializers"""

    def test_student_profile_serializer_valid_data(self):
        """Test StudentProfileSerializer with valid data"""
        from student_app.serializers import StudentProfileSerializer

        data = {
            'username': 'newstudent',
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'newstudent@testschool.com',
            'password': 'newpass123',
            'school': 'Test School',
            'admission_number': 'STU004',
            'date_of_birth': '2018-03-15',
            'parent_name': 'New Parent',
            'parent_email': 'newparent@example.com',
            'parent_contact': '5555555555',
            'address': 'New Address',
            'class_level': self.class_level.id,
            'academic_year': '2024-2025'
        }

        with tenant_context(self.tenant):
            serializer = StudentProfileSerializer(data=data)
            self.assertTrue(serializer.is_valid())

            student_data = serializer.save()
            self.assertEqual(student_data['username'], 'newstudent')
            self.assertEqual(student_data['admission_number'], 'STU004')

    def test_student_profile_serializer_duplicate_admission(self):
        """Test StudentProfileSerializer with duplicate admission number"""
        from student_app.serializers import StudentProfileSerializer

        data = {
            'username': 'anotherstudent',
            'first_name': 'Another',
            'last_name': 'Student',
            'email': 'anotherstudent@testschool.com',
            'password': 'newpass123',
            'school': 'Test School',
            'admission_number': 'STU001',  # Already exists
            'date_of_birth': '2018-03-15',
            'parent_name': 'Another Parent',
            'parent_email': 'anotherparent@example.com',
            'parent_contact': '5555555555',
            'address': 'Another Address',
            'class_level': self.class_level.id,
            'academic_year': '2024-2025'
        }

        with tenant_context(self.tenant):
            serializer = StudentProfileSerializer(data=data)
            # Should be valid at serializer level
            self.assertTrue(serializer.is_valid())

            # Should raise exception at database level
            with self.assertRaises(Exception):
                serializer.save()
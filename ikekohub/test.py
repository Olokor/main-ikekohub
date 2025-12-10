
from django.test import TestCase
from django.contrib.auth import get_user_model
from django_tenants.test.cases import TenantTestCase
from django_tenants.test.client import TenantClient
from django_tenants.utils import tenant_context
from public_app.models import School, Domain, TenantUser
from admin_app.models import AdminProfile
from teacher_app.models import TeacherProfile
from student_app.models import StudentProfile
from parent_app.models import ParentProfile
from report_module.models import (
    Subject, ClassLevel
)

class BaseTestCase(TestCase):
    """Base test case for public schema tests"""

    @classmethod
    def setUpTestData(cls):
        cls.User = get_user_model()

    def setUp(self):
        self.school_data = {
            'name': 'Test School',
            'admin_email': 'admin@testschool.com',
            'admin_first_name': 'John',
            'admin_last_name': 'Doe',
            'schema_name': 'test_school'
        }


class BaseTenantTestCase(TenantTestCase):
    """Base test case for tenant-specific tests"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test school tenant
        cls.school = School.objects.create(
            name='Test School',
            schema_name='test_school',
            admin_email='admin@testschool.com',
            admin_first_name='John',
            admin_last_name='Doe'
        )
        cls.domain = Domain.objects.create(
            domain='testschool.localhost',
            tenant=cls.school,
            is_primary=True
        )
        cls.tenant = cls.school

    def setUp(self):
        super().setUp()
        self.client = TenantClient(self.tenant)

        # Create test users within tenant context
        with tenant_context(self.tenant):
            self.admin_user = TenantUser.objects.create_user(
                username='admin_test',
                email='admin_test@testschool.com',
                password='testpass123',
                school=self.school,
                first_name='Admin',
                last_name='Test'
            )

            self.teacher_user = TenantUser.objects.create_user(
                username='teacher_test',
                email='teacher_test@testschool.com',
                password='testpass123',
                school=self.school,
                first_name='Teacher',
                last_name='Test'
            )

            self.student_user = TenantUser.objects.create_user(
                username='student_test',
                email='student_test@testschool.com',
                password='testpass123',
                school=self.school,
                first_name='Student',
                last_name='Test'
            )

            self.parent_user = TenantUser.objects.create_user(
                username='parent_test',
                email='parent_test@testschool.com',
                password='testpass123',
                school=self.school,
                first_name='Parent',
                last_name='Test'
            )

            # Create profiles
            self.admin_profile = AdminProfile.objects.create(
                user=self.admin_user,
                department='Administration'
            )

            self.class_level = ClassLevel.objects.create(
                name='Grade 1',
                code='G1',
                age_range='6-7 years'
            )

            self.subject = Subject.objects.create(
                name='Mathematics',
                code='MATH',
                description='Basic mathematics',
                class_levels=['Grade 1']
            )

            self.teacher_profile = TeacherProfile.objects.create(
                user=self.teacher_user,
                class_level=self.class_level,
                subject_taught=['Mathematics']
            )

            self.student_profile = StudentProfile.objects.create(
                user=self.student_user,
                admission_number='STU001',
                date_of_birth='2018-01-01',
                parent_name='Parent Test',
                parent_contact='1234567890',
                parent_email='parent_test@testschool.com',
                address='123 Test Street',
                class_level=self.class_level,
                academic_year='2024-2025'
            )

            self.parent_profile = ParentProfile.objects.create(
                user=self.parent_user,
                occupation='Engineer'
            )
            self.parent_profile.children.add(self.student_profile)

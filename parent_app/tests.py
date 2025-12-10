from ikekohub.test import BaseTenantTestCase
from django_tenants.utils import tenant_context

from parent_app.models import ParentProfile
from public_app.models import TenantUser


class ParentProfileModelTests(BaseTenantTestCase):
    """Tests for ParentProfile model"""

    def test_create_parent_profile_success(self):
        """Test successful parent profile creation"""
        with tenant_context(self.tenant):
            user = TenantUser.objects.create_user(
                username='newparent',
                email='newparent@testschool.com',
                password='testpass123',
                school=self.school
            )

            profile = ParentProfile.objects.create(
                user=user,
                occupation='Doctor'
            )

            self.assertEqual(profile.user, user)
            self.assertEqual(profile.occupation, 'Doctor')
            self.assertEqual(profile.role, 'parent')

    def test_parent_children_relationship(self):
        """Test parent-children many-to-many relationship"""
        with tenant_context(self.tenant):
            # Create additional student
            student_user2 = TenantUser.objects.create_user(
                username='student2',
                email='student2@testschool.com',
                password='testpass123',
                school=self.school
            )

            student_profile2 = StudentProfile.objects.create(
                user=student_user2,
                admission_number='STU002',
                date_of_birth='2019-01-01',
                parent_name='Parent Test',
                parent_contact='1234567890',
                parent_email='parent_test@testschool.com',
                address='123 Test Street',
                class_level=self.class_level,
                academic_year='2024-2025'
            )

            # Add both children to parent
            self.parent_profile.children.add(self.student_profile)
            self.parent_profile.children.add(student_profile2)

            self.assertEqual(self.parent_profile.children.count(), 2)
            self.assertIn(self.student_profile, self.parent_profile.children.all())
            self.assertIn(student_profile2, self.parent_profile.children.all())

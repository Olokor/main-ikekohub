from ikekohub.test import BaseTestCase, BaseTenantTestCase
from public_app.models import Domain, TenantUser, School
from django_tenants.utils import tenant_context

from report_module.models import Attendance, ClassLevel, DailyReport, TermReport, Rubric, Subject
from student_app.models import StudentProfile


class SchoolModelTests(BaseTestCase):
    """Tests for School model"""

    def test_create_school_success(self):
        """Test successful school creation"""
        school = School.objects.create(**self.school_data)
        self.assertEqual(school.name, 'Test School')
        self.assertEqual(school.admin_email, 'admin@testschool.com')
        self.assertTrue(school.auto_create_schema)

    def test_school_name_unique_constraint(self):
        """Test school name uniqueness"""
        School.objects.create(**self.school_data)
        with self.assertRaises(Exception):
            School.objects.create(**self.school_data)

    def test_schema_name_validation(self):
        """Test schema name validation"""
        invalid_data = self.school_data.copy()
        invalid_data['schema_name'] = 'invalid-schema-name!'
        with self.assertRaises(Exception):
            School.objects.create(**invalid_data)


class TenantUserModelTests(BaseTestCase):
    """Tests for TenantUser model"""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(**self.school_data)

    def test_create_user_success(self):
        """Test successful user creation"""
        user = TenantUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            school=self.school
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.school, self.school)

    def test_email_case_insensitive_uniqueness(self):
        """Test case-insensitive email uniqueness"""
        TenantUser.objects.create_user(
            username='user1',
            email='TEST@example.com',
            password='testpass123',
            school=self.school
        )

        with self.assertRaises(Exception):
            TenantUser.objects.create_user(
                username='user2',
                email='test@example.com',  # Different case
                password='testpass123',
                school=self.school
            )

    def test_email_validation(self):
        """Test email validation"""
        with self.assertRaises(Exception):
            user = TenantUser(
                username='testuser',
                email='invalid-email',
                school=self.school
            )
            user.full_clean()


class DomainModelTests(BaseTestCase):
    """Tests for Domain model"""

    def setUp(self):
        super().setUp()
        self.school = School.objects.create(**self.school_data)

    def test_create_domain_success(self):
        """Test successful domain creation"""
        domain = Domain.objects.create(
            domain='testschool.localhost',
            tenant=self.school,
            is_primary=True
        )
        self.assertEqual(domain.domain, 'testschool.localhost')
        self.assertTrue(domain.is_primary)

    def test_domain_uniqueness(self):
        """Test domain uniqueness constraint"""
        Domain.objects.create(
            domain='testschool.localhost',
            tenant=self.school,
            is_primary=True
        )

        with self.assertRaises(Exception):
            Domain.objects.create(
                domain='testschool.localhost',  # Duplicate
                tenant=self.school,
                is_primary=False
            )


class EdgeCaseTests(BaseTenantTestCase):
    """Tests for edge cases and error conditions"""

    def test_user_creation_with_extremely_long_fields(self):
        """Test user creation with maximum field lengths"""
        with tenant_context(self.tenant):
            long_username = 'x' * 150  # Within Django's default limit
            long_email = 'x' * 240 + '@test.com'  # Close to 255 limit

            user = TenantUser.objects.create_user(
                username=long_username,
                email=long_email,
                password='testpass123',
                school=self.school
            )

            self.assertEqual(user.username, long_username)
            self.assertEqual(user.email, long_email)

    def test_student_creation_with_special_characters(self):
        """Test student creation with special characters in names"""
        with tenant_context(self.tenant):
            user = TenantUser.objects.create_user(
                username='special_student',
                email='special@testschool.com',
                password='testpass123',
                school=self.school
            )

            profile = StudentProfile.objects.create(
                user=user,
                admission_number="STU'005",
                date_of_birth='2018-01-01',
                parent_name="O'Connor-Smith",
                parent_contact='+1-234-567-8900',
                parent_email='oconnor@example.com',
                address='123 Main St., Apt. #4B',
                class_level=self.class_level,
                academic_year='2024-2025'
            )

            self.assertEqual(profile.parent_name, "O'Connor-Smith")
            self.assertEqual(profile.admission_number, "STU'005")

    def test_attendance_edge_cases(self):
        """Test attendance with edge cases"""
        from datetime import date, time

        with tenant_context(self.tenant):
            # Attendance with no time_in/time_out
            attendance1 = Attendance.objects.create(
                student=self.student_profile,
                date=date(2024, 12, 25),  # Christmas day
                status=Attendance.AttendanceStatus.ABSENT,
                recorded_by=self.teacher_profile,
                notes='Holiday - school closed'
            )

            self.assertIsNone(attendance1.time_in)
            self.assertIsNone(attendance1.time_out)

            # Attendance with very early time
            attendance2 = Attendance.objects.create(
                student=self.student_profile,
                date=date(2024, 1, 2),
                status=Attendance.AttendanceStatus.LATE,
                time_in=time(11, 59, 59),
                recorded_by=self.teacher_profile,
                notes='Very late arrival'
            )

            self.assertEqual(attendance2.time_in, time(11, 59, 59))

    def test_daily_report_toddler_specific_fields(self):
        """Test daily report with toddler-specific fields"""
        from datetime import date

        with tenant_context(self.tenant):
            # Create toddler class
            toddler_class = ClassLevel.objects.create(
                name='Toddler',
                code='TOD',
                age_range='2-3 years',
                is_toddler_class=True
            )

            # Create toddler student
            toddler_user = TenantUser.objects.create_user(
                username='toddler',
                email='toddler@testschool.com',
                password='testpass123',
                school=self.school
            )

            toddler_profile = StudentProfile.objects.create(
                user=toddler_user,
                admission_number='TOD001',
                date_of_birth='2022-01-01',
                parent_name='Toddler Parent',
                parent_contact='1234567890',
                parent_email='toddlerparent@example.com',
                address='Toddler Address',
                class_level=toddler_class,
                academic_year='2024-2025'
            )

            # Create daily report with toddler fields
            report = DailyReport.objects.create(
                student=toddler_profile,
                teacher=self.teacher_profile,
                date=date.today(),
                class_level=toddler_class,
                general_notes='Great day in toddler class',
                mood_behavior='Happy and playful',
                potty_activities='Used potty 3 times successfully',
                meal_notes='Ate all lunch, loved the fruit',
                nap_time='12:30 PM - 2:00 PM',
                diaper_changes=2
            )

            self.assertEqual(report.potty_activities, 'Used potty 3 times successfully')
            self.assertEqual(report.diaper_changes, 2)
            self.assertEqual(report.nap_time, '12:30 PM - 2:00 PM')

    def test_term_report_grade_calculation_edge_cases(self):
        """Test term report grade calculation with edge cases"""
        from report_module.models import TermSubjectReport

        with tenant_context(self.tenant):
            # Create term report
            term_report = TermReport.objects.create(
                student=self.student_profile,
                teacher=self.teacher_profile,
                academic_year='2024-2025',
                term=TermReport.TermChoices.FIRST,
                class_level=self.class_level,
                total_school_days=100,
                days_present=95,
                days_absent=5,
                days_late=0,
                behavior_rating='excellent',
                teacher_comment='Great student'
            )

            # Test edge case scores
            edge_cases = [
                (100, 100, 100, 'A+'),  # Perfect scores
                (0, 0, 0, 'F'),  # Minimum scores
                (95, 95, 95, 'A+'),  # Boundary A+
                (94.9, 94.9, 94.9, 'A'),  # Just below A+
                (60, 60, 60, 'D'),  # Minimum passing
                (59.9, 59.9, 59.9, 'F')  # Just failing
            ]

            for exam, continuous, participation, expected_grade in edge_cases:
                subject_report = TermSubjectReport.objects.create(
                    term_report=term_report,
                    subject=self.subject,
                    exam_score=exam,
                    continuous_assessment=continuous,
                    class_participation=participation,
                    overall_rubric=Rubric.MASTERED,
                    subject_comment='Test comment'
                )

                self.assertEqual(subject_report.grade, expected_grade)

                # Clean up for next iteration
                subject_report.delete()

    def test_zero_division_attendance_percentage(self):
        """Test attendance percentage calculation with zero total days"""
        with tenant_context(self.tenant):
            term_report = TermReport.objects.create(
                student=self.student_profile,
                teacher=self.teacher_profile,
                academic_year='2024-2025',
                term=TermReport.TermChoices.FIRST,
                class_level=self.class_level,
                total_school_days=0,  # Edge case: zero days
                days_present=0,
                days_absent=0,
                days_late=0,
                behavior_rating='good',
                teacher_comment='No school days recorded'
            )

            self.assertEqual(term_report.attendance_percentage, 0)

    def test_negative_attendance_values(self):
        """Test handling of negative attendance values"""
        with tenant_context(self.tenant):
            # This should be caught by validators in a real implementation
            with self.assertRaises(Exception):
                term_report = TermReport(
                    student=self.student_profile,
                    teacher=self.teacher_profile,
                    academic_year='2024-2025',
                    term=TermReport.TermChoices.FIRST,
                    class_level=self.class_level,
                    total_school_days=100,
                    days_present=-5,  # Negative value
                    days_absent=5,
                    days_late=0,
                    behavior_rating='good',
                    teacher_comment='Test'
                )
                term_report.full_clean()


# ==========================
# INTEGRATION TESTS
# ==========================

class IntegrationTests(BaseTenantTestCase):
    """Integration tests for complete workflows"""

    def test_complete_student_lifecycle(self):
        """Test complete student lifecycle from creation to deletion"""
        with tenant_context(self.tenant):
            # 1. Create student
            student_user = TenantUser.objects.create_user(
                username='lifecycle_student',
                email='lifecycle@testschool.com',
                password='testpass123',
                school=self.school
            )

            student_profile = StudentProfile.objects.create(
                user=student_user,
                admission_number='LIFE001',
                date_of_birth='2018-01-01',
                parent_name='Lifecycle Parent',
                parent_contact='1234567890',
                parent_email='lifecycleparent@example.com',
                address='Lifecycle Address',
                class_level=self.class_level,
                academic_year='2024-2025'
            )

            # 2. Verify parent was created (via signal)
            parent_exists = TenantUser.objects.filter(
                email='lifecycleparent@example.com'
            ).exists()
            self.assertTrue(parent_exists)

            # 3. Create attendance record
            from datetime import date
            attendance = Attendance.objects.create(
                student=student_profile,
                date=date.today(),
                status=Attendance.AttendanceStatus.PRESENT,
                recorded_by=self.teacher_profile
            )

            # 4. Create daily report
            daily_report = DailyReport.objects.create(
                student=student_profile,
                teacher=self.teacher_profile,
                date=date.today(),
                class_level=self.class_level,
                general_notes='Good day',
                mood_behavior='Happy'
            )

            # 5. Create term report
            term_report = TermReport.objects.create(
                student=student_profile,
                teacher=self.teacher_profile,
                academic_year='2024-2025',
                term=TermReport.TermChoices.FIRST,
                class_level=self.class_level,
                total_school_days=90,
                days_present=85,
                days_absent=5,
                days_late=0,
                behavior_rating='good',
                teacher_comment='Good progress'
            )

            # 6. Verify all records exist
            self.assertTrue(Attendance.objects.filter(student=student_profile).exists())
            self.assertTrue(DailyReport.objects.filter(student=student_profile).exists())
            self.assertTrue(TermReport.objects.filter(student=student_profile).exists())

            # 7. Delete student and verify cascading deletion
            student_id = student_profile.id
            user_id = student_user.id

            student_profile.delete()

            # Verify related records are deleted
            self.assertFalse(Attendance.objects.filter(student_id=student_id).exists())
            self.assertFalse(DailyReport.objects.filter(student_id=student_id).exists())
            self.assertFalse(TermReport.objects.filter(student_id=student_id).exists())
            self.assertFalse(TenantUser.objects.filter(id=user_id).exists())

    def test_multi_tenant_isolation(self):
        """Test that tenant data is properly isolated"""
        # Create second tenant
        school2 = School.objects.create(
            name='Second School',
            schema_name='second_school',
            admin_email='admin@secondschool.com',
            admin_first_name='Jane',
            admin_last_name='Smith'
        )

        domain2 = Domain.objects.create(
            domain='secondschool.localhost',
            tenant=school2,
            is_primary=True
        )

        # Create user in first tenant
        with tenant_context(self.tenant):
            user1 = TenantUser.objects.create_user(
                username='tenant1_user',
                email='tenant1@testschool.com',
                password='testpass123',
                school=self.school
            )

            student1 = StudentProfile.objects.create(
                user=user1,
                admission_number='T1_STU001',
                date_of_birth='2018-01-01',
                parent_name='Tenant 1 Parent',
                parent_contact='1111111111',
                parent_email='t1parent@example.com',
                address='Tenant 1 Address',
                class_level=self.class_level,
                academic_year='2024-2025'
            )

            # Count records in first tenant
            tenant1_students = StudentProfile.objects.count()

        # Create user in second tenant
        with tenant_context(school2):
            # Create class level for second tenant
            class_level2 = ClassLevel.objects.create(
                name='Grade 1',
                code='G1',
                age_range='6-7 years'
            )

            user2 = TenantUser.objects.create_user(
                username='tenant2_user',
                email='tenant2@secondschool.com',
                password='testpass123',
                school=school2
            )

            student2 = StudentProfile.objects.create(
                user=user2,
                admission_number='T2_STU001',
                date_of_birth='2018-01-01',
                parent_name='Tenant 2 Parent',
                parent_contact='2222222222',
                parent_email='t2parent@example.com',
                address='Tenant 2 Address',
                class_level=class_level2,
                academic_year='2024-2025'
            )

            # Count records in second tenant
            tenant2_students = StudentProfile.objects.count()

        # Verify isolation - each tenant should only see its own data
        self.assertEqual(tenant1_students, 2)  # Original + new student
        self.assertEqual(tenant2_students, 1)  # Only new student

        # Verify same admission numbers can exist in different tenants
        with tenant_context(self.tenant):
            self.assertTrue(
                StudentProfile.objects.filter(admission_number='T1_STU001').exists()
            )
            self.assertFalse(
                StudentProfile.objects.filter(admission_number='T2_STU001').exists()
            )

    def test_concurrent_user_creation(self):
        """Test concurrent user creation scenarios"""
        from django.db import transaction, IntegrityError

        with tenant_context(self.tenant):
            def create_duplicate_user():
                return TenantUser.objects.create_user(
                    username='concurrent',
                    email='concurrent@testschool.com',
                    password='testpass123',
                    school=self.school
                )

            # First creation should succeed
            user1 = create_duplicate_user()
            self.assertIsNotNone(user1.id)

            # Second creation with same email should fail
            with self.assertRaises(IntegrityError):
                create_duplicate_user()

    def test_null_and_empty_field_handling(self):
        """Test handling of null and empty fields"""
        with tenant_context(self.tenant):
            # Test subject with empty description
            subject = Subject.objects.create(
                name='Test Subject',
                code='TEST',
                description='',  # Empty string
                class_levels=[]  # Empty list
            )

            self.assertEqual(subject.description, '')
            self.assertEqual(subject.class_levels, [])

            # Test student with minimal required fields
            user = TenantUser.objects.create_user(
                username='minimal',
                email='minimal@testschool.com',
                password='testpass123',
                school=self.school
            )

            student = StudentProfile.objects.create(
                user=user,
                admission_number='MIN001',
                date_of_birth='2018-01-01',
                parent_name='Minimal Parent',
                parent_contact='1111111111',
                parent_email='minimal@example.com',
                address='',  # Empty address
                class_level=None,  # Null class level
                academic_year='2024-2025'
            )

            self.assertEqual(student.address, '')
            self.assertIsNone(student.class_level)

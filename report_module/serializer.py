# report_module/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from decimal import Decimal
from django.apps import apps
from .models import (
    Subject, ClassLevel, Attendance, DailyReport, DailySubjectReport,
    WeeklyReport, WeeklySubjectSummary, TermReport, TermSubjectReport
)


# Use apps.get_model to avoid circular imports
def get_student_profile_model():
    return apps.get_model('student_app', 'StudentProfile')


def get_teacher_profile_model():
    return apps.get_model('teacher_app', 'TeacherProfile')


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class ClassLevelSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)
    subject_count = serializers.IntegerField(source='subjects.count', read_only=True)

    class Meta:
        model = ClassLevel
        fields = '__all__'


# ========== ATTENDANCE SERIALIZERS ==========

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_username = serializers.CharField(source='student.user.username', read_only=True)
    student_admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.user.get_full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'student', 'student_name', 'student_username', 'student_admission_number',
            'date', 'status', 'time_in', 'time_out', 'notes',
            'recorded_by', 'recorded_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['recorded_by']

    def create(self, validated_data):
        validated_data['recorded_by'] = self.context['request'].user.teacher_profile
        return super().create(validated_data)


class AttendanceBulkSerializer(serializers.Serializer):
    """Serializer for bulk attendance marking"""
    date = serializers.DateField()
    attendance_records = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of {'student_id': int, 'status': str, 'time_in': str, 'notes': str}"
    )

    def validate_attendance_records(self, value):
        StudentProfile = get_student_profile_model()
        for item in value:
            if 'student_id' not in item or 'status' not in item:
                raise serializers.ValidationError("Each record must have student_id and status")

            # Validate student exists
            try:
                StudentProfile.objects.get(id=item['student_id'])
            except StudentProfile.DoesNotExist:
                raise serializers.ValidationError(f"Student with ID {item['student_id']} does not exist")

            # Validate status
            if item['status'] not in dict(Attendance.AttendanceStatus.choices):
                raise serializers.ValidationError(f"Invalid status: {item['status']}")

        return value

    @transaction.atomic
    def create(self, validated_data):
        StudentProfile = get_student_profile_model()
        teacher = self.context['request'].user.teacher_profile
        date = validated_data['date']
        attendance_records = []

        for item in validated_data['attendance_records']:
            student = StudentProfile.objects.get(id=item['student_id'])

            # Update or create attendance record
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=date,
                defaults={
                    'status': item['status'],
                    'time_in': item.get('time_in'),
                    'time_out': item.get('time_out'),
                    'notes': item.get('notes', ''),
                    'recorded_by': teacher
                }
            )
            attendance_records.append(attendance)

        return attendance_records


class AttendanceReportSerializer(serializers.Serializer):
    """Serializer for attendance reports"""
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    student_id = serializers.IntegerField(required=False)
    class_level = serializers.CharField(required=False)

    def validate(self, data):
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data


# ========== DAILY REPORT SERIALIZERS ==========

class DailySubjectReportSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)

    class Meta:
        model = DailySubjectReport
        fields = [
            'id', 'subject', 'subject_name', 'subject_code', 'topics_covered',
            'learning_objectives', 'rubric_rating', 'performance_notes',
            'activities_completed', 'engagement_level', 'created_at'
        ]


class DailyReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    class_level_name = serializers.CharField(source='class_level.name', read_only=True)
    is_toddler_class = serializers.BooleanField(source='class_level.is_toddler_class', read_only=True)
    subject_reports = DailySubjectReportSerializer(many=True, read_only=True)

    # Write-only fields for creating subject reports
    subjects_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of subject report data"
    )

    class Meta:
        model = DailyReport
        fields = [
            'id', 'student', 'student_name', 'student_admission_number',
            'teacher', 'teacher_name', 'date', 'class_level', 'class_level_name', 'is_toddler_class',
            'general_notes', 'mood_behavior', 'social_interaction',
            'potty_activities', 'meal_notes', 'nap_time', 'diaper_changes',
            'homework_completed', 'homework_notes',
            'parent_message', 'requires_parent_action', 'parent_action_required',
            'subject_reports', 'subjects_data',
            'created_at', 'updated_at', 'sent_to_parent', 'sent_at'
        ]
        read_only_fields = ['teacher']

    def validate(self, data):
        # Check if report already exists for this student and date
        if not self.instance:  # Only check on creation
            if DailyReport.objects.filter(
                    student=data.get('student'),
                    date=data.get('date')
            ).exists():
                raise serializers.ValidationError("Daily report already exists for this student on this date")

        return data

    @transaction.atomic
    def create(self, validated_data):
        subjects_data = validated_data.pop('subjects_data', [])
        validated_data['teacher'] = self.context['request'].user.teacher_profile

        # Get class level from student if not provided
        if not validated_data.get('class_level'):
            # Assuming you have a way to get class level from student
            # You might need to add a class_level field to StudentProfile
            raise serializers.ValidationError("Class level is required")

        daily_report = super().create(validated_data)

        # Create subject reports
        for subject_data in subjects_data:
            DailySubjectReport.objects.create(
                daily_report=daily_report,
                **subject_data
            )

        return daily_report

    @transaction.atomic
    def update(self, instance, validated_data):
        subjects_data = validated_data.pop('subjects_data', [])

        # Handle sent_to_parent flag
        if validated_data.get('sent_to_parent') and not instance.sent_to_parent:
            validated_data['sent_at'] = timezone.now()

        instance = super().update(instance, validated_data)

        # Update subject reports if provided
        if subjects_data:
            # Delete existing subject reports
            instance.subject_reports.all().delete()

            # Create new ones
            for subject_data in subjects_data:
                DailySubjectReport.objects.create(
                    daily_report=instance,
                    **subject_data
                )

        return instance


# ========== WEEKLY REPORT SERIALIZERS ==========

class WeeklySubjectSummarySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)

    class Meta:
        model = WeeklySubjectSummary
        fields = [
            'id', 'subject', 'subject_name', 'subject_code', 'topics_covered',
            'overall_rubric_rating', 'progress_notes', 'improvement_areas',
            'created_at'
        ]


class WeeklyReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    class_level_name = serializers.CharField(source='class_level.name', read_only=True)
    subject_summaries = WeeklySubjectSummarySerializer(many=True, read_only=True)

    # Calculated field for total week days
    total_week_days = serializers.SerializerMethodField()

    # Write-only fields for creating subject summaries
    subjects_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of subject summary data"
    )

    class Meta:
        model = WeeklyReport
        fields = [
            'id', 'student', 'student_name', 'student_admission_number',
            'teacher', 'teacher_name', 'week_start_date', 'week_end_date',
            'class_level', 'class_level_name', 'weekly_summary', 'strengths',
            'areas_for_improvement', 'behavioral_summary', 'academic_highlights',
            'homework_completion_rate', 'days_present', 'days_absent', 'days_late',
            'total_week_days', 'home_support_suggestions', 'next_week_focus',
            'additional_notes', 'subject_summaries', 'subjects_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['teacher']

    def get_total_week_days(self, obj):
        return obj.days_present + obj.days_absent + obj.days_late

    def validate(self, data):
        if data.get('week_end_date') and data.get('week_start_date'):
            if data['week_end_date'] <= data['week_start_date']:
                raise serializers.ValidationError("Week end date must be after start date")

            # Check if it's actually a week (7 days)
            week_diff = (data['week_end_date'] - data['week_start_date']).days
            if week_diff != 6:  # 6 days difference means 7 days total
                raise serializers.ValidationError("Week must be exactly 7 days (Sunday to Saturday)")

        # Validate attendance numbers
        total_days = data.get('days_present', 0) + data.get('days_absent', 0) + data.get('days_late', 0)
        if total_days > 7:
            raise serializers.ValidationError("Total attendance days cannot exceed 7 days")

        return data

    @transaction.atomic
    def create(self, validated_data):
        subjects_data = validated_data.pop('subjects_data', [])
        validated_data['teacher'] = self.context['request'].user.teacher_profile

        weekly_report = super().create(validated_data)

        # Create subject summaries
        for subject_data in subjects_data:
            WeeklySubjectSummary.objects.create(
                weekly_report=weekly_report,
                **subject_data
            )

        return weekly_report

    @transaction.atomic
    def update(self, instance, validated_data):
        subjects_data = validated_data.pop('subjects_data', [])
        instance = super().update(instance, validated_data)

        # Update subject summaries if provided
        if subjects_data:
            instance.subject_summaries.all().delete()
            for subject_data in subjects_data:
                WeeklySubjectSummary.objects.create(
                    weekly_report=instance,
                    **subject_data
                )

        return instance


# ========== TERM REPORT SERIALIZERS ==========

class TermSubjectReportSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)

    class Meta:
        model = TermSubjectReport
        fields = [
            'id', 'subject', 'subject_name', 'subject_code',
            'exam_score', 'continuous_assessment', 'class_participation',
            'total_score', 'grade', 'overall_rubric', 'subject_comment',
            'key_topics_mastered', 'topics_needing_work', 'created_at'
        ]
        read_only_fields = ['total_score', 'grade']

    def validate(self, data):
        # Validate scores are within 0-100 range
        for field in ['exam_score', 'continuous_assessment', 'class_participation']:
            if field in data:
                score = data[field]
                if score < 0 or score > 100:
                    raise serializers.ValidationError({field: "Score must be between 0 and 100"})
        return data


class TermReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_admission_number = serializers.CharField(source='student.admission_number', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    class_level_name = serializers.CharField(source='class_level.name', read_only=True)
    subject_reports = TermSubjectReportSerializer(many=True, read_only=True)

    # Calculated fields
    overall_average = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()

    # Write-only fields for creating subject reports
    subjects_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of subject report data"
    )

    class Meta:
        model = TermReport
        fields = [
            'id', 'student', 'student_name', 'student_admission_number',
            'teacher', 'teacher_name', 'academic_year', 'term',
            'class_level', 'class_level_name', 'total_school_days',
            'days_present', 'days_absent', 'days_late', 'attendance_percentage',
            'attendance_rate', 'overall_grade', 'overall_average', 'behavior_rating',
            'teacher_comment', 'principal_comment', 'strengths',
            'areas_for_improvement', 'recommendations', 'promoted_to_next_level',
            'promotion_notes', 'subject_reports', 'subjects_data',
            'finalized', 'finalized_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['teacher', 'attendance_percentage', 'finalized_at']

    def get_overall_average(self, obj):
        """Calculate overall average from subject reports"""
        subject_reports = obj.subject_reports.all()
        if not subject_reports:
            return None

        total_score = sum(report.total_score for report in subject_reports)
        return round(total_score / len(subject_reports), 2)

    def get_attendance_rate(self, obj):
        """Return formatted attendance rate"""
        return f"{obj.attendance_percentage}%"

    def validate(self, data):
        # Validate attendance numbers
        total_school_days = data.get('total_school_days', 0)
        days_present = data.get('days_present', 0)
        days_absent = data.get('days_absent', 0)
        days_late = data.get('days_late', 0)

        if total_school_days > 0:
            total_attendance = days_present + days_absent + days_late
            if total_attendance > total_school_days:
                raise serializers.ValidationError(
                    "Total attendance days cannot exceed total school days"
                )

        # Check if term report already exists (on creation only)
        if not self.instance:
            student = data.get('student')
            academic_year = data.get('academic_year')
            term = data.get('term')

            if student and academic_year and term:
                if TermReport.objects.filter(
                        student=student,
                        academic_year=academic_year,
                        term=term
                ).exists():
                    raise serializers.ValidationError(
                        f"Term report already exists for {student.user.get_full_name()} "
                        f"for {term} term {academic_year}"
                    )

        return data

    @transaction.atomic
    def create(self, validated_data):
        subjects_data = validated_data.pop('subjects_data', [])
        validated_data['teacher'] = self.context['request'].user.teacher_profile

        term_report = super().create(validated_data)

        # Create subject reports
        for subject_data in subjects_data:
            TermSubjectReport.objects.create(
                term_report=term_report,
                **subject_data
            )

        return term_report

    @transaction.atomic
    def update(self, instance, validated_data):
        subjects_data = validated_data.pop('subjects_data', [])

        # Handle finalization
        if validated_data.get('finalized') and not instance.finalized:
            validated_data['finalized_at'] = timezone.now()
        elif not validated_data.get('finalized', True):
            validated_data['finalized_at'] = None

        instance = super().update(instance, validated_data)

        # Update subject reports if provided
        if subjects_data:
            instance.subject_reports.all().delete()
            for subject_data in subjects_data:
                TermSubjectReport.objects.create(
                    term_report=instance,
                    **subject_data
                )

        return instance


# ========== SUMMARY/REPORT ANALYSIS SERIALIZERS ==========

class StudentAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for student attendance summary"""
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    admission_number = serializers.CharField()
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    attendance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class ClassAttendanceSummarySerializer(serializers.Serializer):
    """Serializer for class-wise attendance summary"""
    class_level = serializers.CharField()
    total_students = serializers.IntegerField()
    average_attendance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    students = StudentAttendanceSummarySerializer(many=True)


class StudentProgressSummarySerializer(serializers.Serializer):
    """Serializer for student academic progress summary"""
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    admission_number = serializers.CharField()
    current_grade = serializers.CharField()
    subject_averages = serializers.DictField()
    overall_average = serializers.DecimalField(max_digits=5, decimal_places=2)
    improvement_areas = serializers.ListField(child=serializers.CharField())
    strengths = serializers.ListField(child=serializers.CharField())


class ReportingDashboardSerializer(serializers.Serializer):
    """Serializer for reporting dashboard data"""
    total_students = serializers.IntegerField()
    reports_pending = serializers.IntegerField()
    reports_completed = serializers.IntegerField()
    average_class_attendance = serializers.DecimalField(max_digits=5, decimal_places=2)
    recent_reports = serializers.ListField()
    upcoming_reports = serializers.ListField()


# ========== BULK OPERATIONS SERIALIZERS ==========

class BulkDailyReportSerializer(serializers.Serializer):
    """Serializer for creating multiple daily reports at once"""
    date = serializers.DateField()
    class_level = serializers.PrimaryKeyRelatedField(queryset=ClassLevel.objects.all())
    reports_data = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of report data for each student"
    )

    def validate_reports_data(self, value):
        StudentProfile = get_student_profile_model()
        student_ids = []
        for report_data in value:
            if 'student_id' not in report_data:
                raise serializers.ValidationError("Each report must have a student_id")

            student_id = report_data['student_id']
            if student_id in student_ids:
                raise serializers.ValidationError(f"Duplicate student_id: {student_id}")
            student_ids.append(student_id)

            # Validate student exists
            try:
                StudentProfile.objects.get(id=student_id)
            except StudentProfile.DoesNotExist:
                raise serializers.ValidationError(f"Student with ID {student_id} does not exist")

        return value

    @transaction.atomic
    def create(self, validated_data):
        StudentProfile = get_student_profile_model()
        teacher = self.context['request'].user.teacher_profile
        date = validated_data['date']
        class_level = validated_data['class_level']
        reports_created = []

        for report_data in validated_data['reports_data']:
            student = StudentProfile.objects.get(id=report_data.pop('student_id'))

            # Remove subjects_data if present for separate processing
            subjects_data = report_data.pop('subjects_data', [])

            daily_report = DailyReport.objects.create(
                student=student,
                teacher=teacher,
                date=date,
                class_level=class_level,
                **report_data
            )

            # Create subject reports
            for subject_data in subjects_data:
                DailySubjectReport.objects.create(
                    daily_report=daily_report,
                    **subject_data
                )

            reports_created.append(daily_report)

        return reports_created


class ReportExportSerializer(serializers.Serializer):
    """Serializer for exporting reports"""
    report_type = serializers.ChoiceField(choices=[
        ('daily', 'Daily Reports'),
        ('weekly', 'Weekly Reports'),
        ('term', 'Term Reports'),
        ('attendance', 'Attendance Reports')
    ])
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    class_level = serializers.CharField(required=False)
    student_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    format = serializers.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV')],
        default='pdf'
    )

    def validate(self, data):
        if data['end_date'] < data['start_date']:
            raise serializers.ValidationError("End date must be after start date")
        return data
# reporting_app/serializers.py
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
from .models import (
    Subject, ClassLevel, Attendance, DailyReport, DailySubjectReport,
    WeeklyReport, WeeklySubjectSummary, TermReport, TermSubjectReport
)
from student_app.models import StudentProfile
from teacher_app.models import TeacherProfile


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

            # Check if it's actually a week
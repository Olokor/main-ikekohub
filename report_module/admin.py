# report_module/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Count
from .models import (
    Subject, ClassLevel, Attendance, DailyReport, DailySubjectReport,
    WeeklyReport, WeeklySubjectSummary, TermReport, TermSubjectReport
)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_admission', 'date', 'status', 'time_in', 'time_out', 'recorded_by_name']
    list_filter = ['status', 'date', 'recorded_by']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']

    def student_name(self, obj):
        return obj.student.user.get_full_name()

    student_name.short_description = 'Student'

    def student_admission(self, obj):
        return obj.student.admission_number

    student_admission.short_description = 'Admission No.'

    def recorded_by_name(self, obj):
        return obj.recorded_by.user.get_full_name()

    recorded_by_name.short_description = 'Recorded By'


class DailySubjectReportInline(admin.TabularInline):
    model = DailySubjectReport
    extra = 0
    readonly_fields = ['created_at']


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_admission', 'date', 'teacher_name', 'class_level', 'sent_to_parent',
                    'sent_at']
    list_filter = ['date', 'class_level', 'sent_to_parent', 'teacher']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'sent_at']
    inlines = [DailySubjectReportInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'teacher', 'date', 'class_level')
        }),
        ('General Observations', {
            'fields': ('general_notes', 'mood_behavior', 'social_interaction')
        }),
        ('Toddler Specific', {
            'fields': ('potty_activities', 'meal_notes', 'nap_time', 'diaper_changes'),
            'classes': ('collapse',)
        }),
        ('Academic Progress', {
            'fields': ('homework_completed', 'homework_notes')
        }),
        ('Parent Communication', {
            'fields': ('parent_message', 'requires_parent_action', 'parent_action_required', 'sent_to_parent',
                       'sent_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def student_name(self, obj):
        return obj.student.user.get_full_name()

    student_name.short_description = 'Student'

    def student_admission(self, obj):
        return obj.student.admission_number

    student_admission.short_description = 'Admission No.'

    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name()

    teacher_name.short_description = 'Teacher'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user', 'teacher__user', 'class_level')


@admin.register(DailySubjectReport)
class DailySubjectReportAdmin(admin.ModelAdmin):
    list_display = ['report_student', 'report_date', 'subject_name', 'rubric_rating', 'engagement_level']
    list_filter = ['rubric_rating', 'engagement_level', 'subject', 'daily_report__date']
    search_fields = ['daily_report__student__user__first_name', 'daily_report__student__user__last_name',
                     'subject__name']
    readonly_fields = ['created_at']

    def report_student(self, obj):
        return obj.daily_report.student.user.get_full_name()

    report_student.short_description = 'Student'

    def report_date(self, obj):
        return obj.daily_report.date

    report_date.short_description = 'Date'

    def subject_name(self, obj):
        return obj.subject.name

    subject_name.short_description = 'Subject'


class WeeklySubjectSummaryInline(admin.TabularInline):
    model = WeeklySubjectSummary
    extra = 0
    readonly_fields = ['created_at']


@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_admission', 'week_start_date', 'week_end_date', 'teacher_name',
                    'class_level']
    list_filter = ['week_start_date', 'class_level', 'teacher']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    date_hierarchy = 'week_start_date'
    readonly_fields = ['created_at', 'updated_at']
    inlines = [WeeklySubjectSummaryInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'teacher', 'week_start_date', 'week_end_date', 'class_level')
        }),
        ('Weekly Summary', {
            'fields': ('weekly_summary', 'strengths', 'areas_for_improvement', 'behavioral_summary')
        }),
        ('Academic Progress', {
            'fields': ('academic_highlights', 'homework_completion_rate')
        }),
        ('Attendance Summary', {
            'fields': ('days_present', 'days_absent', 'days_late')
        }),
        ('Recommendations', {
            'fields': ('home_support_suggestions', 'next_week_focus', 'additional_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def student_name(self, obj):
        return obj.student.user.get_full_name()

    student_name.short_description = 'Student'

    def student_admission(self, obj):
        return obj.student.admission_number

    student_admission.short_description = 'Admission No.'

    def teacher_name(self, obj):
        return obj.teacher.user.get_full_name()

    teacher_name.short_description = 'Teacher'


class TermSubjectReportInline(admin.TabularInline):
    model = TermSubjectReport
    extra = 0
    readonly_fields = ['total_score', 'grade', 'created_at']


@admin.register(TermReport)
class TermReportAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'student_admission', 'academic_year', 'term', 'overall_grade',
                    'attendance_percentage', 'finalized', 'finalized_at']
    list_filter = ['academic_year', 'term', 'overall_grade', 'finalized', 'behavior_rating', 'promoted_to_next_level']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'student__admission_number']
    readonly_fields = ['attendance_percentage', 'created_at', 'updated_at', 'finalized_at']
    inlines = [TermSubjectReportInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'teacher', 'academic_year', 'term', 'class_level')
        }),
        ('Attendance Summary', {
            'fields': ('total_school_days', 'days_present', 'days_absent', 'days_late', 'attendance_percentage')
        }),
        ('Performance Summary', {
            'fields': ('overall_grade', 'behavior_rating')
        }),
        ('Comments & Assessment', {
            'fields': ('teacher_comment', 'principal_comment', 'strengths', 'areas_for_improvement', 'recommendations')
        }),
        ('Promotion Status', {
            'fields': ('promoted_to_next_level', 'promotion_notes')
        }),
        ('Report Status', {
            'fields': ('finalized', 'finalized_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def student_name(self, obj):
        return obj.student.user.get_full_name()

    student_name.short_description = 'Student'

    def student_admission(self, obj):
        return obj.student.admission_number

    student_admission.short_description = 'Admission No.'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student__user', 'teacher__user', 'class_level')

    actions = ['finalize_reports', 'unfinalize_reports']

    def finalize_reports(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(finalized=False).update(finalized=True, finalized_at=timezone.now())
        self.message_user(request, f'{updated} reports were finalized.')

    finalize_reports.short_description = "Finalize selected reports"

    def unfinalize_reports(self, request, queryset):
        updated = queryset.filter(finalized=True).update(finalized=False, finalized_at=None)
        self.message_user(request, f'{updated} reports were unfinalized.')

    unfinalize_reports.short_description = "Unfinalize selected reports"


@admin.register(TermSubjectReport)
class TermSubjectReportAdmin(admin.ModelAdmin):
    list_display = ['report_student', 'report_academic_year', 'report_term', 'subject_name',
                    'exam_score', 'total_score', 'grade', 'overall_rubric']
    list_filter = ['grade', 'overall_rubric', 'subject', 'term_report__academic_year', 'term_report__term']
    search_fields = ['term_report__student__user__first_name', 'term_report__student__user__last_name', 'subject__name']
    readonly_fields = ['total_score', 'grade', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('term_report', 'subject')
        }),
        ('Scores', {
            'fields': ('exam_score', 'continuous_assessment', 'class_participation', 'total_score', 'grade')
        }),
        ('Assessment', {
            'fields': ('overall_rubric', 'subject_comment')
        }),
        ('Learning Progress', {
            'fields': ('key_topics_mastered', 'topics_needing_work')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def report_student(self, obj):
        return obj.term_report.student.user.get_full_name()

    report_student.short_description = 'Student'

    def report_academic_year(self, obj):
        return obj.term_report.academic_year

    report_academic_year.short_description = 'Academic Year'

    def report_term(self, obj):
        return obj.term_report.get_term_display()

    report_term.short_description = 'Term'

    def subject_name(self, obj):
        return obj.subject.name

    subject_name.short_description = 'Subject'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'term_report__student__user', 'subject', 'term_report'
        )


# Custom admin views for reports and analytics
class ReportingAdminMixin:
    """Mixin for adding reporting functionality to admin views"""

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('attendance-summary/', self.admin_site.admin_view(self.attendance_summary_view),
                 name='attendance_summary'),
            path('academic-summary/', self.admin_site.admin_view(self.academic_summary_view),
                 name='academic_summary'),
        ]
        return custom_urls + urls

    def attendance_summary_view(self, request):
        from django.shortcuts import render
        from django.db.models import Count, Q
        from datetime import datetime, timedelta

        # Get attendance summary for the last 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        attendance_summary = Attendance.objects.filter(
            date__range=[start_date, end_date]
        ).aggregate(
            total_records=Count('id'),
            present_count=Count('id', filter=Q(status='present')),
            absent_count=Count('id', filter=Q(status='absent')),
            late_count=Count('id', filter=Q(status='late'))
        )

        context = {
            'title': 'Attendance Summary (Last 30 Days)',
            'summary': attendance_summary,
            'date_range': f"{start_date} to {end_date}",
        }

        return render(request, 'admin/attendance_summary.html', context)

    def academic_summary_view(self, request):
        from django.shortcuts import render
        from django.db.models import Avg

        # Get academic performance summary
        academic_summary = TermSubjectReport.objects.aggregate(
            avg_exam_score=Avg('exam_score'),
            avg_total_score=Avg('total_score'),
            total_reports=Count('id')
        )

        # Grade distribution
        grade_distribution = TermSubjectReport.objects.values('grade').annotate(
            count=Count('grade')
        ).order_by('grade')

        context = {
            'title': 'Academic Performance Summary',
            'academic_summary': academic_summary,
            'grade_distribution': list(grade_distribution),
        }

        return render(request, 'admin/academic_summary.html', context)


# Apply the mixin to existing admin classes if needed
# This would typically be done by extending the existing admin classesadmin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'class_levels_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at']

    def class_levels_count(self, obj):
        return len(obj.class_levels) if obj.class_levels else 0

    class_levels_count.short_description = 'Class Levels'


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'age_range', 'is_toddler_class', 'students_count', 'subjects_count', 'created_at']
    list_filter = ['is_toddler_class', 'created_at']
    search_fields = ['name', 'code']
    filter_horizontal = ['subjects']
    readonly_fields = ['created_at']

    def students_count(self, obj):
        return obj.student_class.count()

    students_count.short_description = 'Students'

    def subjects_count(self, obj):
        return obj.subjects.count()

    subjects_count.short_description = 'Subjects'



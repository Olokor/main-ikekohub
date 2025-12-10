from django.contrib import admin
from django.utils import timezone
from django.forms import ModelForm, ValidationError

from .models import (
    Subject, Topic, Department, ClassLevel, AcademicYear, ReportSettings
)


# Simple admin configuration to avoid dependency issues during initial setup
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'order', 'is_active', 'created_at')
    list_filter = ('subject', 'is_active', 'created_at')
    search_fields = ('name', 'subject__name', 'description')
    readonly_fields = ('created_at',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'age_range', 'is_toddler_class', 'created_at')
    list_filter = ('department', 'is_toddler_class', 'created_at')
    search_fields = ('name', 'code')
    filter_horizontal = ('subjects',)
    readonly_fields = ('created_at',)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date', 'is_current', 'created_at')
    list_filter = ('is_current', 'start_date')
    search_fields = ('year',)
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('year', 'start_date', 'end_date', 'is_current')
        }),
        ('Term Dates', {
            'fields': (
                ('first_term_start', 'first_term_end'),
                ('second_term_start', 'second_term_end'),
                ('third_term_start', 'third_term_end')
            )
        }),
    )


# Custom form for ReportSettings with validation
class ReportSettingsForm(ModelForm):
    class Meta:
        model = ReportSettings
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        ca_weight = cleaned_data.get('continuous_assessment_weight', 0)
        cp_weight = cleaned_data.get('class_participation_weight', 0)
        fa_weight = cleaned_data.get('final_assessment_weight', 0)

        if ca_weight + cp_weight + fa_weight != 100:
            raise ValidationError("Assessment weights must add up to 100%")
        return cleaned_data


@admin.register(ReportSettings)
class ReportSettingsAdmin(admin.ModelAdmin):
    form = ReportSettingsForm

    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'school_logo')
        }),
        ('Grading System', {
            'fields': ('grading_scale',)
        }),
        ('Assessment Weights', {
            'fields': ('continuous_assessment_weight', 'class_participation_weight', 'final_assessment_weight'),
            'description': 'These weights must add up to 100%'
        }),
        ('Report Settings', {
            'fields': ('auto_send_daily_reports', 'require_approval_for_term_reports')
        }),
        ('Notifications', {
            'fields': ('send_email_notifications', 'send_sms_notifications')
        }),
        ('Deadlines', {
            'fields': ('daily_report_deadline_time', 'weekly_report_deadline_day')
        }),
    )

    def has_add_permission(self, request):
        # Only allow one settings instance
        return not ReportSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False


# Custom admin site configuration
admin.site.site_header = 'School Reports Administration'
admin.site.site_title = 'School Reports Admin'
admin.site.index_title = 'Welcome to School Reports Administration'

# NOTE: Additional admin classes for models that reference other apps should be added
# AFTER the related apps are properly set up and their models are available.
# You can create a separate admin file or add them here later.
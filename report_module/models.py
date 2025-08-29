# report_module/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from public_app.models import TenantUser


class Subject(models.Model):
    """Subjects offered in the school"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    class_levels = models.JSONField(default=list, help_text="List of class levels this subject is offered")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassLevel(models.Model):
    """Class levels in the school (e.g., Toddler, Pre-K, Grade 1, etc.)"""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    age_range = models.CharField(max_length=20, help_text="e.g., '2-3 years'")
    is_toddler_class = models.BooleanField(default=False, help_text="Special reports for toddler classes")
    subjects = models.ManyToManyField(Subject, related_name='class_levels_offered', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Rubric(models.TextChoices):
    """Learning rubric choices"""
    INTRODUCED = 'introduced', 'Introduced'
    WORKING = 'working', 'Working'
    MASTERED = 'mastered', 'Mastered'
    NOT_APPLICABLE = 'not_applicable', 'Not Applicable'


class Attendance(models.Model):
    """Daily attendance tracking"""

    class AttendanceStatus(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'
        LATE = 'late', 'Late'
        EXCUSED = 'excused', 'Excused'

    # Use string reference to avoid circular import
    student = models.ForeignKey('student_app.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes about attendance")
    # Use string reference to avoid circular import
    recorded_by = models.ForeignKey('teacher_app.TeacherProfile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.student.user.username} - {self.date} - {self.status}"


class DailyReport(models.Model):
    """Daily reports sent by teachers to parents"""
    # Use string references to avoid circular imports
    student = models.ForeignKey('student_app.StudentProfile', on_delete=models.CASCADE, related_name='daily_reports')
    teacher = models.ForeignKey('teacher_app.TeacherProfile', on_delete=models.CASCADE, related_name='daily_reports_created')
    date = models.DateField()
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    # General daily activities
    general_notes = models.TextField(help_text="General observations about the student's day")
    mood_behavior = models.CharField(max_length=200, help_text="Student's mood and behavior")
    social_interaction = models.TextField(blank=True, help_text="How student interacted with peers")

    # Toddler-specific fields (only shown for toddler classes)
    potty_activities = models.TextField(blank=True, help_text="Potty training updates (for toddler classes)")
    meal_notes = models.TextField(blank=True, help_text="Eating habits and meal notes")
    nap_time = models.CharField(max_length=100, blank=True, help_text="Nap time details")
    diaper_changes = models.IntegerField(null=True, blank=True, help_text="Number of diaper changes")

    # Academic progress
    homework_completed = models.BooleanField(default=False)
    homework_notes = models.TextField(blank=True)

    # Parent communication
    parent_message = models.TextField(blank=True, help_text="Specific message for parents")
    requires_parent_action = models.BooleanField(default=False)
    parent_action_required = models.TextField(blank=True, help_text="What action parent needs to take")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_to_parent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['teacher', 'date']),
            models.Index(fields=['class_level', 'date']),
        ]

    def __str__(self):
        return f"Daily Report - {self.student.user.username} - {self.date}"


class DailySubjectReport(models.Model):
    """Subject-specific learning for daily reports"""
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='subject_reports')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # What was taught
    topics_covered = models.JSONField(default=list, help_text="List of topics/subtopics covered")
    learning_objectives = models.TextField(help_text="What the student was expected to learn")

    # Student performance
    rubric_rating = models.CharField(max_length=20, choices=Rubric.choices, default=Rubric.INTRODUCED)
    performance_notes = models.TextField(help_text="Specific notes about student's performance in this subject")

    # Activities and engagement
    activities_completed = models.JSONField(default=list, help_text="List of activities completed")
    engagement_level = models.CharField(
        max_length=20,
        choices=[
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
            ('not_engaged', 'Not Engaged')
        ],
        default='medium'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['daily_report', 'subject']

    def __str__(self):
        return f"{self.daily_report.student.user.username} - {self.subject.name} - {self.daily_report.date}"


class WeeklyReport(models.Model):
    """Weekly summary reports"""
    # Use string references to avoid circular imports
    student = models.ForeignKey('student_app.StudentProfile', on_delete=models.CASCADE, related_name='weekly_reports')
    teacher = models.ForeignKey('teacher_app.TeacherProfile', on_delete=models.CASCADE, related_name='weekly_reports_created')
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    # Summary fields
    weekly_summary = models.TextField(help_text="Overall summary of the week")
    strengths = models.TextField(help_text="Student's strengths observed this week")
    areas_for_improvement = models.TextField(help_text="Areas that need attention")
    behavioral_summary = models.TextField(help_text="Summary of behavior patterns")

    # Academic progress
    academic_highlights = models.TextField(help_text="Key academic achievements")
    homework_completion_rate = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of homework completed",
        default=0
    )

    # Attendance summary for the week
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_late = models.IntegerField(default=0)

    # Parent recommendations
    home_support_suggestions = models.TextField(blank=True, help_text="Suggestions for parents to support at home")
    next_week_focus = models.TextField(help_text="What to focus on next week")

    # Additional updates
    additional_notes = models.TextField(blank=True, help_text="Any additional updates for parents")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'week_start_date']
        indexes = [
            models.Index(fields=['student', 'week_start_date']),
            models.Index(fields=['teacher', 'week_start_date']),
        ]

    def __str__(self):
        return f"Weekly Report - {self.student.user.username} - Week of {self.week_start_date}"


class WeeklySubjectSummary(models.Model):
    """Subject summaries for weekly reports"""
    weekly_report = models.ForeignKey(WeeklyReport, on_delete=models.CASCADE, related_name='subject_summaries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    topics_covered = models.JSONField(default=list, help_text="Topics covered during the week")
    overall_rubric_rating = models.CharField(max_length=20, choices=Rubric.choices)
    progress_notes = models.TextField(help_text="Progress in this subject during the week")
    improvement_areas = models.TextField(blank=True, help_text="Areas needing improvement in this subject")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['weekly_report', 'subject']

    def __str__(self):
        return f"{self.weekly_report.student.user.username} - {self.subject.name} - Week {self.weekly_report.week_start_date}"


class TermReport(models.Model):
    """End of term comprehensive reports"""

    class TermChoices(models.TextChoices):
        FIRST = 'first', 'First Term'
        SECOND = 'second', 'Second Term'
        THIRD = 'third', 'Third Term'

    # Use string references to avoid circular imports
    student = models.ForeignKey('student_app.StudentProfile', on_delete=models.CASCADE, related_name='term_reports')
    teacher = models.ForeignKey('teacher_app.TeacherProfile', on_delete=models.CASCADE, related_name='term_reports_created')
    academic_year = models.CharField(max_length=20, help_text="e.g., 2024-2025")
    term = models.CharField(max_length=10, choices=TermChoices.choices)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    # Attendance summary for the term
    total_school_days = models.IntegerField()
    days_present = models.IntegerField()
    days_absent = models.IntegerField()
    days_late = models.IntegerField()
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    # Overall performance
    overall_grade = models.CharField(
        max_length=2,
        choices=[
            ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
            ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
            ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
            ('D+', 'D+'), ('D', 'D'), ('F', 'F'),
        ],
        blank=True
    )

    # Behavioral assessment
    behavior_rating = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('satisfactory', 'Satisfactory'),
            ('needs_improvement', 'Needs Improvement'),
        ]
    )

    # Comments
    teacher_comment = models.TextField(help_text="Teacher's overall comment for the term")
    principal_comment = models.TextField(blank=True, help_text="Principal's comment")

    # Recommendations
    strengths = models.TextField(help_text="Student's key strengths")
    areas_for_improvement = models.TextField(help_text="Areas that need improvement")
    recommendations = models.TextField(help_text="Recommendations for next term")

    # Promotion status
    promoted_to_next_level = models.BooleanField(default=True)
    promotion_notes = models.TextField(blank=True, help_text="Notes about promotion decision")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['student', 'academic_year', 'term']
        indexes = [
            models.Index(fields=['student', 'academic_year', 'term']),
            models.Index(fields=['teacher', 'academic_year', 'term']),
        ]

    def save(self, *args, **kwargs):
        # Auto-calculate attendance percentage
        if self.total_school_days > 0:
            self.attendance_percentage = (self.days_present / self.total_school_days) * 100

        # Set finalized timestamp
        if self.finalized and not self.finalized_at:
            self.finalized_at = timezone.now()
        elif not self.finalized:
            self.finalized_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Term Report - {self.student.user.username} - {self.term} {self.academic_year}"


class TermSubjectReport(models.Model):
    """Subject-specific performance for term reports"""
    term_report = models.ForeignKey(TermReport, on_delete=models.CASCADE, related_name='subject_reports')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # Scores (out of 100)
    exam_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Exam score out of 100"
    )
    continuous_assessment = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Continuous assessment score out of 100"
    )
    class_participation = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Class participation score out of 100"
    )

    # Calculated total (auto-computed)
    total_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        editable=False
    )

    # Grade (auto-computed based on total score)
    grade = models.CharField(
        max_length=2,
        choices=[
            ('A+', 'A+'), ('A', 'A'), ('A-', 'A-'),
            ('B+', 'B+'), ('B', 'B'), ('B-', 'B-'),
            ('C+', 'C+'), ('C', 'C'), ('C-', 'C-'),
            ('D+', 'D+'), ('D', 'D'), ('F', 'F'),
        ],
        editable=False
    )

    # Rubric assessment
    overall_rubric = models.CharField(max_length=20, choices=Rubric.choices)

    # Performance notes
    subject_comment = models.TextField(help_text="Teacher's comment on subject performance")
    key_topics_mastered = models.JSONField(default=list, help_text="List of topics student mastered")
    topics_needing_work = models.JSONField(default=list, help_text="List of topics needing more work")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['term_report', 'subject']

    def calculate_grade(self, score):
        """Calculate letter grade based on numerical score"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 87:
            return 'A-'
        elif score >= 84:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 77:
            return 'B-'
        elif score >= 74:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 67:
            return 'C-'
        elif score >= 64:
            return 'D+'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def save(self, *args, **kwargs):
        # Auto-calculate total score (weighted average)
        # 60% exam, 25% continuous assessment, 15% participation
        self.total_score = (
                (self.exam_score * 0.60) +
                (self.continuous_assessment * 0.25) +
                (self.class_participation * 0.15)
        )

        # Auto-calculate grade
        self.grade = self.calculate_grade(self.total_score)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.term_report.student.user.username} - {self.subject.name} - {self.term_report.term}"
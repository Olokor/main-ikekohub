from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class Subject(models.Model):
    """Main subjects offered in the school (e.g., Mathematics, English, Science)"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


class Topic(models.Model):
    """Sub-subjects/topics/milestones under each main subject"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='sub_subjects')
    name = models.CharField(max_length=200, help_text="e.g., 'Addition and Subtraction', 'Reading Comprehension'")
    # code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    class_levels = models.JSONField(
        default=list,
        help_text="List of class levels where this sub-subject is taught"
    )
    order = models.PositiveIntegerField(default=0, help_text="Order of teaching this sub-subject")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject.name} - {self.name}"

    class Meta:
        ordering = ['subject__name', 'order', 'name']
        unique_together = ['subject']


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class ClassLevel(models.Model):
    """Class levels in the school (e.g., Toddler, Pre-K, Grade 1, etc.)"""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    age_range = models.CharField(max_length=20, help_text="e.g., '2-3 years'", blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    is_toddler_class = models.BooleanField(default=False, help_text="Special reports for toddler classes")
    subjects = models.ManyToManyField(Subject, related_name='class_levels_offered', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class LearningRubric(models.TextChoices):
    """Learning assessment rubric choices"""
    INTRODUCED = 'introduced', 'Introduced'
    WORKING = 'working', 'Working'
    MASTERED = 'mastered', 'Mastered'
    NOT_APPLICABLE = 'not_applicable', 'Not Applicable'


class Attendance(models.Model):
    """Daily attendance tracking for students"""

    class AttendanceStatus(models.TextChoices):
        PRESENT = 'present', 'Present'
        ABSENT = 'absent', 'Absent'


    student = models.ForeignKey(
        'student_app.StudentProfile',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT
    )
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes about attendance")
    recorded_by = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='recorded_attendance'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'date']
        indexes = [
            models.Index(fields=['student', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date} - {self.get_status_display()}"


class DailyReport(models.Model):
    """Daily learning reports for what the child learned that day"""
    student = models.ForeignKey(
        'student_app.StudentProfile',
        on_delete=models.CASCADE,
        related_name='daily_reports'
    )
    teacher = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='daily_reports_created'
    )
    date = models.DateField()
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    # General daily observations
    general_notes = models.TextField(
        blank=True,
        help_text="General observations about the student's day"
    )
    mood_behavior = models.CharField(
        max_length=200,
        blank=True,
        help_text="Student's mood and behavior"
    )
    social_interaction = models.TextField(
        blank=True,
        help_text="How student interacted with peers"
    )

    # Toddler-specific fields (only for toddler classes)
    potty_activities = models.TextField(
        blank=True,
        help_text="Potty training updates (for toddler classes)"
    )
    meal_notes = models.TextField(
        blank=True,
        help_text="Eating habits and meal notes"
    )
    nap_time = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nap time details"
    )
    diaper_changes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Number of diaper changes"
    )

    # Academic engagement
    homework_completed = models.BooleanField(default=False)
    homework_notes = models.TextField(blank=True)

    # Parent communication
    parent_message = models.TextField(
        blank=True,
        help_text="Specific message for parents"
    )
    requires_parent_action = models.BooleanField(default=False)
    parent_action_required = models.TextField(
        blank=True,
        help_text="What action parent needs to take"
    )

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
        return f"Daily Report - {self.student.user.get_full_name()} - {self.date}"


class DailySubSubjectReport(models.Model):
    """Daily learning for specific sub-subjects/topics/milestones"""
    daily_report = models.ForeignKey(
        DailyReport,
        on_delete=models.CASCADE,
        related_name='sub_subject_reports'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    sub_subject = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='daily_reports'
    )

    # Learning assessment
    rubric_rating = models.CharField(
        max_length=20,
        choices=LearningRubric.choices,
        default=LearningRubric.INTRODUCED
    )

    # Activities and what was taught
    activities_completed = models.JSONField(
        default=list,
        help_text="List of specific activities completed for this sub-subject"
    )
    learning_objectives = models.TextField(
        help_text="What the student was expected to learn in this sub-subject"
    )

    # Performance notes (optional)
    performance_comment = models.TextField(
        blank=True,
        help_text="Optional comment about student's performance in this sub-subject"
    )

    # Engagement level
    engagement_level = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('needs_attention', 'Needs Attention')
        ],
        default='good'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['daily_report', 'sub_subject']
        ordering = ['sub_subject__order', 'sub_subject__name']

    def __str__(self):
        return f"{self.daily_report.student.user.get_full_name()} - {self.sub_subject.name} - {self.daily_report.date}"


class WeeklyReport(models.Model):
    """Weekly summary reports with compulsory comments"""
    student = models.ForeignKey(
        'student_app.StudentProfile',
        on_delete=models.CASCADE,
        related_name='weekly_reports'
    )
    subjects = models.JSONField(default=list)
    teacher = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='weekly_reports_created'
    )
    week_start_date = models.DateField()
    week_end_date = models.DateField()
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    # COMPULSORY weekly summary fields
    weekly_summary = models.TextField(
        help_text="REQUIRED: Overall summary of the week's learning and development"
    )
    strengths_observed = models.TextField(
        help_text="REQUIRED: Student's strengths observed this week"
    )
    areas_for_improvement = models.TextField(
        help_text="REQUIRED: Areas that need attention and improvement"
    )
    behavioral_summary = models.TextField(
        help_text="REQUIRED: Summary of behavior patterns throughout the week"
    )

    # Academic progress summary
    academic_highlights = models.TextField(
        help_text="REQUIRED: Key academic achievements and progress"
    )
    homework_completion_summary = models.TextField(
        help_text="Summary of homework completion and quality"
    )

    # Attendance summary for the week
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_late = models.IntegerField(default=0)

    # Parent engagement and recommendations
    home_support_suggestions = models.TextField(
        help_text="REQUIRED: Specific suggestions for parents to support learning at home"
    )
    next_week_focus = models.TextField(
        help_text="REQUIRED: What to focus on in the coming week"
    )

    # Additional notes
    special_achievements = models.TextField(
        blank=True,
        help_text="Any special achievements or milestones reached this week"
    )
    concerns_or_challenges = models.TextField(
        blank=True,
        help_text="Any concerns or challenges that parents should be aware of"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'week_start_date']
        indexes = [
            models.Index(fields=['student', 'week_start_date']),
            models.Index(fields=['teacher', 'week_start_date']),
        ]

    def __str__(self):
        return f"Weekly Report - {self.student.user.get_full_name()} - Week of {self.week_start_date}"


class WeeklySubSubjectSummary(models.Model):
    """Weekly sub-subject learning summaries"""
    weekly_report = models.ForeignKey(
        WeeklyReport,
        on_delete=models.CASCADE,
        related_name='sub_subject_summaries'
    )
    sub_subject = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='weekly_summaries'
    )

    # Weekly assessment
    weekly_rubric_rating = models.CharField(
        max_length=20,
        choices=LearningRubric.choices,
        help_text="Overall assessment for this sub-subject during the week"
    )

    # Weekly progress and activities
    topics_activities_covered = models.JSONField(
        default=list,
        help_text="Specific topics and activities covered during the week"
    )

    # COMPULSORY weekly comment
    weekly_progress_comment = models.TextField(
        help_text="REQUIRED: Detailed comment on student's progress in this sub-subject during the week"
    )

    improvement_recommendations = models.TextField(
        blank=True,
        help_text="Specific recommendations for improvement in this sub-subject"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['weekly_report', 'sub_subject']
        ordering = ['sub_subject__subject__name', 'sub_subject__order']

    def __str__(self):
        return f"{self.weekly_report.student.user.get_full_name()} - {self.sub_subject.name} - Week {self.weekly_report.week_start_date}"


class TermReport(models.Model):
    """Comprehensive end of term reports"""

    class TermChoices(models.TextChoices):
        FIRST = 'first', 'First Term'
        SECOND = 'second', 'Second Term'
        THIRD = 'third', 'Third Term'

    class BehaviorRating(models.TextChoices):
        EXCELLENT = 'excellent', 'Excellent'
        VERY_GOOD = 'very_good', 'Very Good'
        GOOD = 'good', 'Good'
        SATISFACTORY = 'satisfactory', 'Satisfactory'
        NEEDS_IMPROVEMENT = 'needs_improvement', 'Needs Improvement'

    student = models.ForeignKey(
        'student_app.StudentProfile',
        on_delete=models.CASCADE,
        related_name='term_reports'
    )
    class_teacher = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='term_reports_as_class_teacher'
    )
    academic_year = models.CharField(max_length=20, help_text="e.g., 2024-2025")
    term = models.CharField(max_length=10, choices=TermChoices.choices)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    # Attendance summary for the term
    total_school_days = models.IntegerField()
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0)
    days_late = models.IntegerField(default=0)
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        editable=False
    )

    # Behavioral assessment
    behavior_rating = models.CharField(
        max_length=20,
        choices=BehaviorRating.choices,
        default=BehaviorRating.GOOD
    )

    # REQUIRED Comments
    class_teacher_comment = models.TextField(
        help_text="REQUIRED: Class teacher's comprehensive comment about the student's overall performance"
    )
    principal_comment = models.TextField(
        help_text="REQUIRED: Principal/Director's comment on the student's development"
    )

    # Overall assessment
    general_strengths = models.TextField(
        help_text="Student's key strengths across all subjects"
    )
    general_areas_for_improvement = models.TextField(
        help_text="General areas that need improvement across subjects"
    )
    overall_recommendations = models.TextField(
        help_text="Overall recommendations for continued development"
    )

    # Term totals and averages (calculated fields)
    overall_average_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Overall average across all subjects"
    )
    overall_grade = models.CharField(
        max_length=2,
        choices=[
            ('A+', 'A+ (95-100)'), ('A', 'A (90-94)'), ('A-', 'A- (85-89)'),
            ('B+', 'B+ (80-84)'), ('B', 'B (75-79)'), ('B-', 'B- (70-74)'),
            ('C+', 'C+ (65-69)'), ('C', 'C (60-64)'), ('C-', 'C- (55-59)'),
            ('D+', 'D+ (50-54)'), ('D', 'D (45-49)'), ('F', 'F (0-44)'),
        ],
        blank=True,
        editable=False
    )

    # Promotion status
    promoted_to_next_level = models.BooleanField(default=True)
    promotion_notes = models.TextField(
        blank=True,
        help_text="Notes about promotion decision if not promoted"
    )

    # Report status
    finalized = models.BooleanField(
        default=False,
        help_text="Once finalized, the report cannot be edited"
    )
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='finalized_term_reports'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'academic_year', 'term']
        indexes = [
            models.Index(fields=['student', 'academic_year', 'term']),
            models.Index(fields=['class_teacher', 'academic_year', 'term']),
        ]

    def calculate_grade(self, score):
        """Calculate letter grade based on numerical score"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 55:
            return 'C-'
        elif score >= 50:
            return 'D+'
        elif score >= 45:
            return 'D'
        else:
            return 'F'

    def save(self, *args, **kwargs):
        # Auto-calculate attendance percentage
        if self.total_school_days > 0:
            self.attendance_percentage = round(
                (self.days_present / self.total_school_days) * 100, 2
            )

        # Calculate overall average from subject reports
        if self.pk:  # Only if report already exists
            subject_reports = self.subject_reports.all()
            if subject_reports.exists():
                total_scores = sum(report.total_score for report in subject_reports)
                self.overall_average_score = round(total_scores / len(subject_reports), 2)
                self.overall_grade = self.calculate_grade(self.overall_average_score)

        # Handle finalization
        if self.finalized and not self.finalized_at:
            self.finalized_at = timezone.now()
        elif not self.finalized:
            self.finalized_at = None
            self.finalized_by = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Term Report - {self.student.user.get_full_name()} - {self.get_term_display()} {self.academic_year}"


class TermSubjectReport(models.Model):
    """Subject-level performance for term reports"""
    term_report = models.ForeignKey(
        TermReport,
        on_delete=models.CASCADE,
        related_name='subject_reports'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    # Score breakdown (totaling 100%)
    continuous_assessment = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Continuous assessment score (40% weight)"
    )
    class_participation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Class participation score (20% weight)"
    )
    final_assessment = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Final assessment/exam score (40% weight)"
    )

    # Calculated total score (40% + 20% + 40%)
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        editable=False,
        help_text="Weighted total: (CA×40% + Participation×20% + Final×40%)"
    )

    # Letter grade (auto-computed from total score)
    letter_grade = models.CharField(
        max_length=2,
        choices=[
            ('A+', 'A+ (95-100)'), ('A', 'A (90-94)'), ('A-', 'A- (85-89)'),
            ('B+', 'B+ (80-84)'), ('B', 'B (75-79)'), ('B-', 'B- (70-74)'),
            ('C+', 'C+ (65-69)'), ('C', 'C (60-64)'), ('C-', 'C- (55-59)'),
            ('D+', 'D+ (50-54)'), ('D', 'D (45-49)'), ('F', 'F (0-44)'),
        ],
        editable=False
    )

    # Subject-specific comments
    subject_teacher_comment = models.TextField(
        help_text="Subject teacher's comment on student's performance"
    )

    # Key strengths and improvement areas for this subject
    subject_strengths = models.TextField(
        help_text="Student's strengths in this particular subject"
    )
    areas_needing_work = models.TextField(
        help_text="Specific areas in this subject that need more work"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['term_report', 'subject']
        ordering = ['subject__name']

    def calculate_total_score(self):
        """Calculate weighted total score"""
        return round(
            (self.continuous_assessment * 0.40) +
            (self.class_participation * 0.20) +
            (self.final_assessment * 0.40),
            2
        )

    def calculate_letter_grade(self, score):
        """Calculate letter grade from total score"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 55:
            return 'C-'
        elif score >= 50:
            return 'D+'
        elif score >= 45:
            return 'D'
        else:
            return 'F'

    def save(self, *args, **kwargs):
        # Auto-calculate total score and grade
        self.total_score = self.calculate_total_score()
        self.letter_grade = self.calculate_letter_grade(self.total_score)
        super().save(*args, **kwargs)

        # Update parent term report's overall average
        self.term_report.save()

    def __str__(self):
        return f"{self.term_report.student.user.get_full_name()} - {self.subject.name} - {self.term_report.get_term_display()}"


class TermSubSubjectAssessment(models.Model):
    """End of term assessment for each sub-subject/milestone"""
    term_subject_report = models.ForeignKey(
        TermSubjectReport,
        on_delete=models.CASCADE,
        related_name='sub_subject_assessments'
    )
    sub_subject = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='term_assessments'
    )

    # Final rubric assessment for the term
    final_rubric_rating = models.CharField(
        max_length=20,
        choices=LearningRubric.choices,
        help_text="Student's final mastery level of this sub-subject for the term"
    )

    # Progress tracking
    progress_throughout_term = models.TextField(
        help_text="How the student progressed in this sub-subject throughout the term"
    )

    # Key achievements
    key_milestones_achieved = models.JSONField(
        default=list,
        help_text="Specific milestones or learning objectives achieved"
    )

    # Areas for continued focus
    areas_for_continued_focus = models.TextField(
        blank=True,
        help_text="Areas in this sub-subject that need continued attention"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['term_subject_report', 'sub_subject']
        ordering = ['sub_subject__order', 'sub_subject__name']

    def __str__(self):
        return f"{self.term_subject_report.term_report.student.user.get_full_name()} - {self.sub_subject.name} - {self.term_subject_report.term_report.get_term_display()}"


# Additional models for better reporting

class ReportTemplate(models.Model):
    """Templates for different types of reports"""

    class TemplateType(models.TextChoices):
        DAILY = 'daily', 'Daily Report'
        WEEKLY = 'weekly', 'Weekly Report'
        TERM = 'term', 'Term Report'

    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=10, choices=TemplateType.choices)
    class_level = models.ForeignKey(
        ClassLevel,
        on_delete=models.CASCADE,
        help_text="Which class level this template is for"
    )

    # Template content (JSON structure defining the format)
    template_structure = models.JSONField(
        default=dict,
        help_text="JSON structure defining the report template"
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.class_level.name} - {self.get_template_type_display()}"

    class Meta:
        ordering = ['template_type', 'class_level__name', 'name']


class ParentFeedback(models.Model):
    """Parent feedback on reports"""

    class FeedbackType(models.TextChoices):
        DAILY = 'daily', 'Daily Report Feedback'
        WEEKLY = 'weekly', 'Weekly Report Feedback'
        TERM = 'term', 'Term Report Feedback'

    # Link to specific reports
    daily_report = models.ForeignKey(
        DailyReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parent_feedbacks'
    )
    weekly_report = models.ForeignKey(
        WeeklyReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parent_feedbacks'
    )
    term_report = models.ForeignKey(
        TermReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='parent_feedbacks'
    )

    parent = models.ForeignKey(
        'parent_app.ParentProfile',
        on_delete=models.CASCADE,
        related_name='report_feedbacks'
    )

    feedback_type = models.CharField(max_length=10, choices=FeedbackType.choices)

    # Feedback content
    feedback_text = models.TextField(help_text="Parent's feedback or questions")
    parent_observations = models.TextField(
        blank=True,
        help_text="Parent's observations from home"
    )

    # Follow-up requests
    requests_meeting = models.BooleanField(
        default=False,
        help_text="Parent requests a meeting with teacher"
    )
    meeting_notes = models.TextField(
        blank=True,
        help_text="Notes from parent-teacher meeting"
    )

    # Response from teacher
    teacher_response = models.TextField(
        blank=True,
        help_text="Teacher's response to parent feedback"
    )
    responded_by = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parent_feedback_responses'
    )
    responded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        report_ref = ""
        if self.daily_report:
            report_ref = f"Daily {self.daily_report.date}"
        elif self.weekly_report:
            report_ref = f"Weekly {self.weekly_report.week_start_date}"
        elif self.term_report:
            report_ref = f"Term {self.term_report.get_term_display()}"

        return f"Feedback: {self.parent.user.get_full_name()} - {report_ref}"

    class Meta:
        ordering = ['-created_at']


class ReportApproval(models.Model):
    """Approval workflow for reports before sending to parents"""

    class ApprovalStatus(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        NEEDS_REVISION = 'needs_revision', 'Needs Revision'

    # Link to different report types
    daily_report = models.OneToOneField(
        DailyReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approval'
    )
    weekly_report = models.OneToOneField(
        WeeklyReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approval'
    )
    term_report = models.OneToOneField(
        TermReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='approval'
    )

    # Approval details
    status = models.CharField(
        max_length=15,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )

    submitted_by = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='submitted_approvals'
    )

    reviewed_by = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_approvals'
    )

    # Approval/rejection notes
    reviewer_notes = models.TextField(
        blank=True,
        help_text="Notes from reviewer about approval/rejection"
    )

    revision_requested = models.TextField(
        blank=True,
        help_text="Specific revisions requested"
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        report_type = ""
        if self.daily_report:
            report_type = f"Daily Report - {self.daily_report.date}"
        elif self.weekly_report:
            report_type = f"Weekly Report - {self.weekly_report.week_start_date}"
        elif self.term_report:
            report_type = f"Term Report - {self.term_report.get_term_display()}"

        return f"Approval: {report_type} - {self.get_status_display()}"

    class Meta:
        ordering = ['-submitted_at']


class LearningGoal(models.Model):
    """Learning goals/objectives for sub-subjects"""
    sub_subject = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='learning_goals'
    )

    goal_description = models.TextField(
        help_text="Specific learning goal or objective"
    )

    # Goal difficulty/complexity level
    complexity_level = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced')
        ],
        default='basic'
    )

    # Expected timeline to achieve this goal
    expected_duration_weeks = models.PositiveIntegerField(
        help_text="Expected number of weeks to achieve this goal"
    )

    # Prerequisites
    prerequisite_goals = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        help_text="Goals that should be achieved before this one"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sub_subject.subject.name} - {self.sub_subject.name} - {self.goal_description[:50]}"

    class Meta:
        ordering = ['sub_subject__subject__name', 'sub_subject__order', 'complexity_level']


class StudentLearningGoalProgress(models.Model):
    """Track individual student progress on specific learning goals"""
    student = models.ForeignKey(
        'student_app.StudentProfile',
        on_delete=models.CASCADE,
        related_name='learning_goal_progress'
    )
    learning_goal = models.ForeignKey(
        LearningGoal,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )

    # Current progress status
    current_status = models.CharField(
        max_length=20,
        choices=LearningRubric.choices,
        default=LearningRubric.INTRODUCED
    )

    # Date when this goal was first introduced to the student
    introduced_date = models.DateField()

    # Date when goal was mastered (if applicable)
    mastered_date = models.DateField(null=True, blank=True)

    # Progress notes
    progress_notes = models.TextField(
        blank=True,
        help_text="Notes about student's progress toward this goal"
    )

    # Teacher tracking this progress
    tracked_by = models.ForeignKey(
        'teacher_app.TeacherProfile',
        on_delete=models.CASCADE,
        related_name='tracked_learning_goals'
    )

    last_assessed_date = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-set mastered_date when status changes to mastered
        if self.current_status == LearningRubric.MASTERED and not self.mastered_date:
            self.mastered_date = timezone.now().date()
        elif self.current_status != LearningRubric.MASTERED:
            self.mastered_date = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.learning_goal.goal_description[:30]} - {self.current_status}"

    class Meta:
        unique_together = ['student', 'learning_goal']
        ordering = ['student__user__first_name', 'learning_goal__sub_subject__subject__name']


class ReportNotification(models.Model):
    """Notifications for parents when reports are available"""

    class NotificationType(models.TextChoices):
        DAILY_REPORT = 'daily', 'Daily Report Available'
        WEEKLY_REPORT = 'weekly', 'Weekly Report Available'
        TERM_REPORT = 'term', 'Term Report Available'
        FEEDBACK_RESPONSE = 'feedback_response', 'Teacher Responded to Feedback'
        MEETING_REQUEST = 'meeting_request', 'Meeting Requested'

    recipient = models.ForeignKey(
        'parent_app.ParentProfile',
        on_delete=models.CASCADE,
        related_name='report_notifications'
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices
    )

    # Link to relevant reports
    daily_report = models.ForeignKey(
        DailyReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    weekly_report = models.ForeignKey(
        WeeklyReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    term_report = models.ForeignKey(
        TermReport,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Notification content
    title = models.CharField(max_length=200)
    message = models.TextField()

    # Status tracking
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification: {self.recipient.user.get_full_name()} - {self.title}"

    class Meta:
        ordering = ['-created_at']


class AcademicYear(models.Model):
    """Academic year configuration"""
    year = models.CharField(
        max_length=20,
        unique=True,
        help_text="e.g., '2024-2025'"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    # Term dates
    first_term_start = models.DateField()
    first_term_end = models.DateField()
    second_term_start = models.DateField()
    second_term_end = models.DateField()
    third_term_start = models.DateField()
    third_term_end = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ensure only one academic year is marked as current
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Academic Year {self.year}" + (" (Current)" if self.is_current else "")

    class Meta:
        ordering = ['-start_date']


class ReportSettings(models.Model):
    """System-wide settings for reports"""

    # Grading system settings
    grading_scale = models.JSONField(
        default=dict,
        help_text="JSON object defining the grading scale and boundaries"
    )

    # Score weights for term reports
    continuous_assessment_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('40.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    class_participation_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    final_assessment_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('40.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # Report sending settings
    auto_send_daily_reports = models.BooleanField(
        default=False,
        help_text="Automatically send daily reports to parents"
    )

    require_approval_for_term_reports = models.BooleanField(
        default=True,
        help_text="Require approval before term reports are sent to parents"
    )

    # Notification settings
    send_email_notifications = models.BooleanField(default=True)
    send_sms_notifications = models.BooleanField(default=False)

    # Report deadlines
    daily_report_deadline_time = models.TimeField(
        default="16:00",
        help_text="Time by which daily reports should be completed"
    )

    weekly_report_deadline_day = models.CharField(
        max_length=10,
        choices=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
        ],
        default='friday'
    )

    # System settings
    school_name = models.CharField(max_length=200, blank=True)
    school_logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Ensure weights add up to 100%
        total_weight = (
                self.continuous_assessment_weight +
                self.class_participation_weight +
                self.final_assessment_weight
        )
        if total_weight != 100:
            raise ValidationError("Assessment weights must add up to 100%")

    def save(self, *args, **kwargs):
        self.full_clean()
        # Ensure only one settings instance exists
        if not self.pk and ReportSettings.objects.exists():
            raise ValidationError("Only one ReportSettings instance is allowed")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Report Settings - {self.school_name or 'School'}"

    class Meta:
        verbose_name = "Report Settings"
        verbose_name_plural = "Report Settings"
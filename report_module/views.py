# report_module/views.py
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db import transaction
from django.core.exceptions import ValidationError
from django.apps import apps

from admin_app.permission import IsSchoolAdmin, AnyOf
from teacher_app.permission import IsTeacher
from student_app.permission import IsStudent

from .models import (
    Subject, Topic, Department, ClassLevel, LearningRubric, Attendance,
    DailyReport, DailySubSubjectReport, WeeklyReport, WeeklySubSubjectSummary,
    TermReport, TermSubjectReport, TermSubSubjectAssessment, ReportTemplate,
    ParentFeedback, ReportApproval, LearningGoal, StudentLearningGoalProgress,
    ReportNotification, AcademicYear, ReportSettings
)

from .serializer import (
    SubjectSerializer, TopicSerializer, DepartmentSerializer, ClassLevelSerializer,
    AttendanceSerializer, BulkAttendanceSerializer, DailyReportSerializer,
    DailySubSubjectReportSerializer, WeeklyReportSerializer, WeeklySubSubjectSummarySerializer,
    TermReportSerializer, TermSubjectReportSerializer, TermSubSubjectAssessmentSerializer,
    ReportTemplateSerializer, ParentFeedbackSerializer, ReportApprovalSerializer,
    LearningGoalSerializer, StudentLearningGoalProgressSerializer,
    ReportNotificationSerializer, AcademicYearSerializer, ReportSettingsSerializer,
    BulkDailyReportSerializer, ReportExportSerializer
)


# Helper functions to avoid circular imports
def get_student_profile_model():
    return apps.get_model('student_app', 'StudentProfile')


def get_teacher_profile_model():
    return apps.get_model('teacher_app', 'TeacherProfile')


def get_parent_profile_model():
    return apps.get_model('parent_app', 'ParentProfile')


# ========== SUBJECT VIEWS ==========

class SubjectListCreateView(generics.ListCreateAPIView):
    """List all subjects or create a new subject"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = Subject.objects.filter(is_active=True)
        class_level = self.request.query_params.get('class_level', None)
        if class_level:
            queryset = queryset.filter(class_levels_offered__name=class_level)
        return queryset.order_by('name')


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a subject"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsSchoolAdmin]


# ========== TOPIC VIEWS ==========

class TopicListCreateView(generics.ListCreateAPIView):
    """List all topics or create a new topic"""
    serializer_class = TopicSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = Topic.objects.filter(is_active=True)
        subject_id = self.request.query_params.get('subject_id', None)
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset.order_by('subject__name', 'order', 'name')


class TopicDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a topic"""
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


# ========== DEPARTMENT VIEWS ==========

class DepartmentListCreateView(generics.ListCreateAPIView):
    """List all departments or create a new one"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a department"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsSchoolAdmin]


# ========== CLASS LEVEL VIEWS ==========

class ClassLevelListCreateView(generics.ListCreateAPIView):
    """List all class levels or create a new one"""
    queryset = ClassLevel.objects.all()
    serializer_class = ClassLevelSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        return ClassLevel.objects.all().order_by('name')


class ClassLevelDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a class level"""
    queryset = ClassLevel.objects.all()
    serializer_class = ClassLevelSerializer
    permission_classes = [IsSchoolAdmin]


# ========== ATTENDANCE VIEWS ==========

class AttendanceListCreateView(generics.ListCreateAPIView):
    """List attendance records or mark attendance"""
    serializer_class = AttendanceSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = Attendance.objects.all()

        # Filter by date
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)

        # Filter by student
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        return queryset.order_by('-date', 'student__user__first_name')

    def perform_create(self, serializer):
        # Get current teacher profile
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            serializer.save(recorded_by=teacher)
        except TeacherProfile.DoesNotExist:
            raise ValidationError("Teacher profile not found")


class AttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an attendance record"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


class BulkAttendanceView(APIView):
    """Mark attendance for multiple students at once"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, *args, **kwargs):
        serializer = BulkAttendanceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attendance_records = serializer.save()
            response_data = AttendanceSerializer(attendance_records, many=True).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendanceReportView(APIView):
    """Generate attendance reports"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, *args, **kwargs):
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        student_id = request.data.get('student_id')
        class_level = request.data.get('class_level')

        if not start_date or not end_date:
            return Response({
                'error': 'start_date and end_date are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        queryset = Attendance.objects.filter(date__range=[start_date, end_date])

        if student_id:
            queryset = queryset.filter(student_id=student_id)

        if class_level:
            queryset = queryset.filter(student__class_level__name=class_level)

        # Generate summary
        summary = queryset.values(
            'student__id',
            'student__user__first_name',
            'student__user__last_name',
            'student__admission_number'
        ).annotate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(status='present')),
            absent_days=Count('id', filter=Q(status='absent'))
        )

        # Calculate attendance rates
        report_data = []
        for item in summary:
            attendance_rate = (item['present_days'] / item['total_days'] * 100) if item['total_days'] > 0 else 0
            report_data.append({
                'student_id': item['student__id'],
                'student_name': f"{item['student__user__first_name']} {item['student__user__last_name']}",
                'admission_number': item['student__admission_number'],
                'total_days': item['total_days'],
                'present_days': item['present_days'],
                'absent_days': item['absent_days'],
                'attendance_rate': round(attendance_rate, 2)
            })

        return Response({
            'period': f"{start_date} to {end_date}",
            'total_records': queryset.count(),
            'students_summary': report_data
        }, status=status.HTTP_200_OK)


# ========== DAILY REPORT VIEWS ==========

class DailyReportListCreateView(generics.ListCreateAPIView):
    """List daily reports or create a new one"""
    serializer_class = DailyReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = DailyReport.objects.all()

        # Filter by date
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)

        # Filter by student
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by teacher (if teacher is making request)
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=teacher)
        except TeacherProfile.DoesNotExist:
            pass

        return queryset.order_by('-date', 'student__user__first_name')

    def perform_create(self, serializer):
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            serializer.save(teacher=teacher)
        except TeacherProfile.DoesNotExist:
            raise ValidationError("Teacher profile not found")


class DailyReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a daily report"""
    serializer_class = DailyReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = DailyReport.objects.all()
        # Teachers can only access their own reports
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=teacher)
        except TeacherProfile.DoesNotExist:
            pass
        return queryset


class DailySubSubjectReportListCreateView(generics.ListCreateAPIView):
    """List or create daily sub-subject reports"""
    serializer_class = DailySubSubjectReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        daily_report_id = self.request.query_params.get('daily_report_id')
        queryset = DailySubSubjectReport.objects.all()

        if daily_report_id:
            queryset = queryset.filter(daily_report_id=daily_report_id)

        return queryset.order_by('sub_subject__order', 'sub_subject__name')


# ========== WEEKLY REPORT VIEWS ==========

class WeeklyReportListCreateView(generics.ListCreateAPIView):
    """List weekly reports or create a new one"""
    serializer_class = WeeklyReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = WeeklyReport.objects.all()

        # Filter by week start date
        week_start = self.request.query_params.get('week_start', None)
        if week_start:
            queryset = queryset.filter(week_start_date=week_start)

        # Filter by student
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        # Filter by teacher (if teacher is making request)
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=teacher)
        except TeacherProfile.DoesNotExist:
            pass

        return queryset.order_by('-week_start_date', 'student__user__first_name')

    def perform_create(self, serializer):
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            serializer.save(teacher=teacher)
        except TeacherProfile.DoesNotExist:
            raise ValidationError("Teacher profile not found")


class WeeklyReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a weekly report"""
    serializer_class = WeeklyReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = WeeklyReport.objects.all()
        # Teachers can only access their own reports
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=teacher)
        except TeacherProfile.DoesNotExist:
            pass
        return queryset


class WeeklySubSubjectSummaryListCreateView(generics.ListCreateAPIView):
    """List or create weekly sub-subject summaries"""
    serializer_class = WeeklySubSubjectSummarySerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        weekly_report_id = self.request.query_params.get('weekly_report_id')
        queryset = WeeklySubSubjectSummary.objects.all()

        if weekly_report_id:
            queryset = queryset.filter(weekly_report_id=weekly_report_id)

        return queryset.order_by('sub_subject__subject__name', 'sub_subject__order')


# ========== TERM REPORT VIEWS ==========

class TermReportListCreateView(generics.ListCreateAPIView):
    """List term reports or create a new one"""
    serializer_class = TermReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = TermReport.objects.all()

        # Filter by academic year
        academic_year = self.request.query_params.get('academic_year', None)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)

        # Filter by term
        term = self.request.query_params.get('term', None)
        if term:
            queryset = queryset.filter(term=term)

        # Filter by student
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        return queryset.order_by('-academic_year', 'term', 'student__user__first_name')

    def perform_create(self, serializer):
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            serializer.save(class_teacher=teacher)
        except TeacherProfile.DoesNotExist:
            raise ValidationError("Teacher profile not found")


class TermReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a term report"""
    queryset = TermReport.objects.all()
    serializer_class = TermReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


class FinalizeTermReportView(APIView):
    """Finalize a term report (prevent further editing)"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, report_id, *args, **kwargs):
        try:
            report = TermReport.objects.get(id=report_id)

            # Check permissions
            TeacherProfile = get_teacher_profile_model()
            try:
                teacher = TeacherProfile.objects.get(user=request.user)
                if not hasattr(request.user, 'admin_profile'):
                    if report.class_teacher != teacher:
                        return Response({
                            'error': 'You can only finalize your own reports'
                        }, status=status.HTTP_403_FORBIDDEN)
            except TeacherProfile.DoesNotExist:
                return Response({
                    'error': 'Teacher profile not found'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if report has subject reports
            if not report.subject_reports.exists():
                return Response({
                    'error': 'Cannot finalize report without subject reports'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                report.finalized = True
                report.finalized_at = timezone.now()
                report.finalized_by = teacher
                report.save()

            return Response({
                'message': 'Term report finalized successfully',
                'finalized_at': report.finalized_at
            }, status=status.HTTP_200_OK)

        except TermReport.DoesNotExist:
            return Response({
                'error': 'Term report not found'
            }, status=status.HTTP_404_NOT_FOUND)


class TermSubjectReportListCreateView(generics.ListCreateAPIView):
    """List or create term subject reports"""
    serializer_class = TermSubjectReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        term_report_id = self.request.query_params.get('term_report_id')
        queryset = TermSubjectReport.objects.all()

        if term_report_id:
            queryset = queryset.filter(term_report_id=term_report_id)

        return queryset.order_by('subject__name')


class TermSubSubjectAssessmentListCreateView(generics.ListCreateAPIView):
    """List or create term sub-subject assessments"""
    serializer_class = TermSubSubjectAssessmentSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        term_subject_report_id = self.request.query_params.get('term_subject_report_id')
        queryset = TermSubSubjectAssessment.objects.all()

        if term_subject_report_id:
            queryset = queryset.filter(term_subject_report_id=term_subject_report_id)

        return queryset.order_by('sub_subject__order', 'sub_subject__name')


# ========== LEARNING GOAL VIEWS ==========

class LearningGoalListCreateView(generics.ListCreateAPIView):
    """List learning goals or create new ones"""
    serializer_class = LearningGoalSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = LearningGoal.objects.filter(is_active=True)

        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(sub_subject__subject_id=subject_id)

        complexity_level = self.request.query_params.get('complexity_level')
        if complexity_level:
            queryset = queryset.filter(complexity_level=complexity_level)

        return queryset.order_by('sub_subject__subject__name', 'complexity_level')


class LearningGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a learning goal"""
    queryset = LearningGoal.objects.all()
    serializer_class = LearningGoalSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


class StudentLearningGoalProgressListCreateView(generics.ListCreateAPIView):
    """Track student progress on learning goals"""
    serializer_class = StudentLearningGoalProgressSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = StudentLearningGoalProgress.objects.all()

        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(current_status=status)

        return queryset.order_by('student__user__first_name', 'learning_goal__sub_subject__subject__name')

    def perform_create(self, serializer):
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            serializer.save(tracked_by=teacher)
        except TeacherProfile.DoesNotExist:
            raise ValidationError("Teacher profile not found")


class StudentLearningGoalProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete student learning goal progress"""
    queryset = StudentLearningGoalProgress.objects.all()
    serializer_class = StudentLearningGoalProgressSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


# ========== REPORT APPROVAL VIEWS ==========

class ReportApprovalListView(generics.ListAPIView):
    """List pending report approvals"""
    serializer_class = ReportApprovalSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = ReportApproval.objects.all()

        status_filter = self.request.query_params.get('status', 'pending')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-submitted_at')


class ApproveReportView(APIView):
    """Approve or reject a report"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, approval_id, *args, **kwargs):
        try:
            approval = ReportApproval.objects.get(id=approval_id)
            action = request.data.get('action')  # 'approve', 'reject', 'needs_revision'
            notes = request.data.get('notes', '')

            if action not in ['approve', 'reject', 'needs_revision']:
                return Response({
                    'error': 'Invalid action. Must be approve, reject, or needs_revision'
                }, status=status.HTTP_400_BAD_REQUEST)

            TeacherProfile = get_teacher_profile_model()
            try:
                teacher = TeacherProfile.objects.get(user=request.user)
            except TeacherProfile.DoesNotExist:
                return Response({
                    'error': 'Teacher profile not found'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                if action == 'approve':
                    approval.status = ReportApproval.ApprovalStatus.APPROVED
                elif action == 'reject':
                    approval.status = ReportApproval.ApprovalStatus.REJECTED
                else:
                    approval.status = ReportApproval.ApprovalStatus.NEEDS_REVISION
                    approval.revision_requested = notes

                approval.reviewed_by = teacher
                approval.reviewed_at = timezone.now()
                approval.reviewer_notes = notes
                approval.save()

            return Response({
                'message': f'Report {action}d successfully',
                'status': approval.get_status_display()
            }, status=status.HTTP_200_OK)

        except ReportApproval.DoesNotExist:
            return Response({
                'error': 'Approval record not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ========== DASHBOARD AND ANALYTICS VIEWS ==========

class ReportingDashboardView(APIView):
    """Get reporting dashboard data"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get(self, request, *args, **kwargs):
        # Get current date info
        today = timezone.now().date()
        current_week_start = today - timedelta(days=today.weekday())
        current_academic_year = f"{today.year}-{today.year + 1}"

        # Basic counts
        StudentProfile = get_student_profile_model()
        total_students = StudentProfile.objects.count()

        # Daily reports stats
        daily_reports_today = DailyReport.objects.filter(date=today).count()
        daily_reports_pending = total_students - daily_reports_today

        # Weekly reports stats
        weekly_reports_current = WeeklyReport.objects.filter(
            week_start_date=current_week_start
        ).count()

        # Term reports stats
        term_reports_finalized = TermReport.objects.filter(
            academic_year=current_academic_year,
            finalized=True
        ).count()

        # Attendance stats
        attendance_today = Attendance.objects.filter(date=today)
        present_today = attendance_today.filter(status='present').count()
        total_attendance_today = attendance_today.count()
        attendance_rate_today = (present_today / total_attendance_today * 100) if total_attendance_today > 0 else 0

        # Recent reports
        recent_daily_reports = DailyReport.objects.filter(
            date__gte=today - timedelta(days=7)
        ).order_by('-date')[:5]

        # Filter by teacher if not admin
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=request.user)
            if not hasattr(request.user, 'admin_profile'):
                recent_daily_reports = recent_daily_reports.filter(teacher=teacher)
        except TeacherProfile.DoesNotExist:
            pass

        recent_reports_data = []
        for report in recent_daily_reports:
            recent_reports_data.append({
                'id': report.id,
                'student_name': report.student.user.get_full_name(),
                'date': report.date,
                'sent_to_parent': report.sent_to_parent
            })

        dashboard_data = {
            'total_students': total_students,
            'daily_reports': {
                'completed_today': daily_reports_today,
                'pending_today': daily_reports_pending
            },
            'weekly_reports': {
                'current_week': weekly_reports_current
            },
            'term_reports': {
                'finalized': term_reports_finalized
            },
            'attendance': {
                'rate_today': round(attendance_rate_today, 2),
                'present_today': present_today,
                'total_today': total_attendance_today
            },
            'recent_reports': recent_reports_data
        }

        return Response(dashboard_data, status=status.HTTP_200_OK)


class StudentProgressAnalyticsView(APIView):
    """Get student progress analytics"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get(self, request, student_id, *args, **kwargs):
        try:
            StudentProfile = get_student_profile_model()
            student = StudentProfile.objects.get(id=student_id)

            # Get term reports for analysis
            term_reports = TermReport.objects.filter(student=student).order_by('-academic_year', 'term')

            # Get attendance summary
            total_attendance = Attendance.objects.filter(student=student).count()
            present_days = Attendance.objects.filter(student=student, status='present').count()
            attendance_rate = (present_days / total_attendance * 100) if total_attendance > 0 else 0

            # Get subject performance trends
            subject_trends = {}
            for report in term_reports:
                for subject_report in report.subject_reports.all():
                    subject_name = subject_report.subject.name
                    if subject_name not in subject_trends:
                        subject_trends[subject_name] = []
                    subject_trends[subject_name].append({
                        'term': f"{report.term} {report.academic_year}",
                        'score': float(subject_report.total_score),
                        'grade': subject_report.letter_grade
                    })

            # Calculate overall trends
            overall_scores = []
            for report in term_reports:
                if report.subject_reports.exists():
                    avg_score = report.subject_reports.aggregate(
                        avg_score=Avg('total_score')
                    )['avg_score']
                    overall_scores.append({
                        'term': f"{report.term} {report.academic_year}",
                        'average_score': round(float(avg_score), 2) if avg_score else 0
                    })

            analytics_data = {
                'student': {
                    'id': student.id,
                    'name': student.user.get_full_name(),
                    'admission_number': student.admission_number,
                    'class_level': student.class_level.name if student.class_level else None
                },
                'attendance': {
                    'total_days': total_attendance,
                    'present_days': present_days,
                    'attendance_rate': round(attendance_rate, 2)
                },
                'academic_performance': {
                    'overall_trends': overall_scores,
                    'subject_trends': subject_trends
                },
                'total_reports': term_reports.count()
            }

            return Response(analytics_data, status=status.HTTP_200_OK)

        except StudentProfile.DoesNotExist:
            return Response({
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ========== PARENT ACCESS VIEWS ==========

class ParentStudentReportsView(APIView):
    """Get reports for parent's children"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Check if user is a parent
        ParentProfile = get_parent_profile_model()
        try:
            parent = ParentProfile.objects.get(user=request.user)
        except ParentProfile.DoesNotExist:
            return Response({
                'error': 'Access denied. Parent account required.'
            }, status=status.HTTP_403_FORBIDDEN)

        children = parent.children.all()

        report_type = request.query_params.get('type', 'daily')  # daily, weekly, term
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        reports_data = []

        for child in children:
            child_data = {
                'student': {
                    'id': child.id,
                    'name': child.user.get_full_name(),
                    'admission_number': child.admission_number,
                    'class_level': child.class_level.name if child.class_level else None
                },
                'reports': []
            }

            if report_type == 'daily':
                reports = DailyReport.objects.filter(student=child, sent_to_parent=True)
                if start_date and end_date:
                    reports = reports.filter(date__range=[start_date, end_date])
                reports = reports.order_by('-date')[:10]  # Last 10 reports
                child_data['reports'] = DailyReportSerializer(reports, many=True).data

            elif report_type == 'weekly':
                reports = WeeklyReport.objects.filter(student=child)
                if start_date and end_date:
                    reports = reports.filter(week_start_date__range=[start_date, end_date])
                reports = reports.order_by('-week_start_date')[:5]  # Last 5 reports
                child_data['reports'] = WeeklyReportSerializer(reports, many=True).data

            elif report_type == 'term':
                reports = TermReport.objects.filter(student=child, finalized=True)
                academic_year = request.query_params.get('academic_year')
                if academic_year:
                    reports = reports.filter(academic_year=academic_year)
                reports = reports.order_by('-academic_year', 'term')
                child_data['reports'] = TermReportSerializer(reports, many=True).data

            reports_data.append(child_data)

        return Response({
            'parent': {
                'name': request.user.get_full_name(),
                'children_count': children.count()
            },
            'report_type': report_type,
            'children_reports': reports_data
        }, status=status.HTTP_200_OK)


# ========== NOTIFICATION VIEWS ==========

class ReportNotificationListView(generics.ListAPIView):
    """List notifications for the authenticated user"""
    serializer_class = ReportNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ParentProfile = get_parent_profile_model()
        try:
            parent = ParentProfile.objects.get(user=self.request.user)
            return ReportNotification.objects.filter(recipient=parent).order_by('-created_at')
        except ParentProfile.DoesNotExist:
            return ReportNotification.objects.none()


class MarkNotificationReadView(APIView):
    """Mark a notification as read"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, notification_id, *args, **kwargs):
        try:
            ParentProfile = get_parent_profile_model()
            parent = ParentProfile.objects.get(user=request.user)

            notification = ReportNotification.objects.get(
                id=notification_id,
                recipient=parent
            )

            notification.read = True
            notification.read_at = timezone.now()
            notification.save()

            return Response({
                'message': 'Notification marked as read'
            }, status=status.HTTP_200_OK)

        except ParentProfile.DoesNotExist:
            return Response({
                'error': 'Parent profile not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        except ReportNotification.DoesNotExist:
            return Response({
                'error': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ========== PARENT FEEDBACK VIEWS ==========

class ParentFeedbackListCreateView(generics.ListCreateAPIView):
    """List parent feedback or create new feedback"""
    serializer_class = ParentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ParentProfile = get_parent_profile_model()
        try:
            parent = ParentProfile.objects.get(user=self.request.user)
            return ParentFeedback.objects.filter(parent=parent).order_by('-created_at')
        except ParentProfile.DoesNotExist:
            return ParentFeedback.objects.none()

    def perform_create(self, serializer):
        ParentProfile = get_parent_profile_model()
        try:
            parent = ParentProfile.objects.get(user=self.request.user)
            serializer.save(parent=parent)
        except ParentProfile.DoesNotExist:
            raise ValidationError("Parent profile not found")


class ParentFeedbackDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete parent feedback"""
    serializer_class = ParentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ParentProfile = get_parent_profile_model()
        try:
            parent = ParentProfile.objects.get(user=self.request.user)
            return ParentFeedback.objects.filter(parent=parent)
        except ParentProfile.DoesNotExist:
            return ParentFeedback.objects.none()


class RespondToParentFeedbackView(APIView):
    """Teacher response to parent feedback"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, feedback_id, *args, **kwargs):
        try:
            feedback = ParentFeedback.objects.get(id=feedback_id)
            response_text = request.data.get('response', '')

            if not response_text:
                return Response({
                    'error': 'Response text is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            TeacherProfile = get_teacher_profile_model()
            try:
                teacher = TeacherProfile.objects.get(user=request.user)
            except TeacherProfile.DoesNotExist:
                return Response({
                    'error': 'Teacher profile not found'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                feedback.teacher_response = response_text
                feedback.responded_by = teacher
                feedback.responded_at = timezone.now()
                feedback.save()

                # Create notification for parent
                ReportNotification.objects.create(
                    recipient=feedback.parent,
                    notification_type=ReportNotification.NotificationType.FEEDBACK_RESPONSE,
                    title=f"Teacher responded to your feedback",
                    message=f"Your teacher has responded to your feedback on {feedback.get_feedback_type_display()}."
                )

            return Response({
                'message': 'Response sent successfully',
                'response_time': feedback.responded_at
            }, status=status.HTTP_200_OK)

        except ParentFeedback.DoesNotExist:
            return Response({
                'error': 'Feedback not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ========== ACADEMIC YEAR & SETTINGS VIEWS ==========

class AcademicYearListCreateView(generics.ListCreateAPIView):
    """List academic years or create new one"""
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [IsSchoolAdmin]


class AcademicYearDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete academic year"""
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
    permission_classes = [IsSchoolAdmin]


class SetCurrentAcademicYearView(APIView):
    """Set an academic year as current"""
    permission_classes = [IsSchoolAdmin]

    def post(self, request, year_id, *args, **kwargs):
        try:
            academic_year = AcademicYear.objects.get(id=year_id)

            with transaction.atomic():
                # Set all others to False
                AcademicYear.objects.update(is_current=False)
                # Set this one to True
                academic_year.is_current = True
                academic_year.save()

            return Response({
                'message': f'Academic year {academic_year.year} set as current',
                'current_year': academic_year.year
            }, status=status.HTTP_200_OK)

        except AcademicYear.DoesNotExist:
            return Response({
                'error': 'Academic year not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ReportSettingsView(APIView):
    """Get or update report settings"""
    permission_classes = [IsSchoolAdmin]

    def get(self, request, *args, **kwargs):
        try:
            settings = ReportSettings.objects.first()
            if not settings:
                settings = ReportSettings.objects.create()

            serializer = ReportSettingsSerializer(settings)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        try:
            settings = ReportSettings.objects.first()
            if not settings:
                settings = ReportSettings.objects.create()

            serializer = ReportSettingsSerializer(settings, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# ========== TEMPLATE VIEWS ==========

class ReportTemplateListCreateView(generics.ListCreateAPIView):
    """List report templates or create new ones"""
    serializer_class = ReportTemplateSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = ReportTemplate.objects.filter(is_active=True)
        template_type = self.request.query_params.get('template_type')
        class_level = self.request.query_params.get('class_level')

        if template_type:
            queryset = queryset.filter(template_type=template_type)
        if class_level:
            queryset = queryset.filter(class_level__name=class_level)

        return queryset.order_by('template_type', 'class_level__name', 'name')

    def perform_create(self, serializer):
        TeacherProfile = get_teacher_profile_model()
        try:
            teacher = TeacherProfile.objects.get(user=self.request.user)
            serializer.save(created_by=teacher)
        except TeacherProfile.DoesNotExist:
            raise ValidationError("Teacher profile not found")


class ReportTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a report template"""
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


# ========== UTILITY VIEWS ==========

class SendDailyReportToParentView(APIView):
    """Send daily report to parent"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, report_id, *args, **kwargs):
        try:
            report = DailyReport.objects.get(id=report_id)

            # Check permissions
            TeacherProfile = get_teacher_profile_model()
            try:
                teacher = TeacherProfile.objects.get(user=request.user)
                if not hasattr(request.user, 'admin_profile'):
                    if report.teacher != teacher:
                        return Response({
                            'error': 'You can only send your own reports'
                        }, status=status.HTTP_403_FORBIDDEN)
            except TeacherProfile.DoesNotExist:
                return Response({
                    'error': 'Teacher profile not found'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Mark as sent
                report.sent_to_parent = True
                report.sent_at = timezone.now()
                report.save()

                # Create notification for parents
                ParentProfile = get_parent_profile_model()
                parents = ParentProfile.objects.filter(children=report.student)

                for parent in parents:
                    ReportNotification.objects.create(
                        recipient=parent,
                        notification_type=ReportNotification.NotificationType.DAILY_REPORT,
                        daily_report=report,
                        title=f"Daily Report Available - {report.student.user.get_full_name()}",
                        message=f"Daily report for {report.date} is now available for {report.student.user.get_full_name()}."
                    )

            return Response({
                'message': 'Daily report sent to parent successfully',
                'sent_at': report.sent_at
            }, status=status.HTTP_200_OK)

        except DailyReport.DoesNotExist:
            return Response({
                'error': 'Daily report not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ClassAttendanceSummaryView(APIView):
    """Get attendance summary by class"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get(self, request, *args, **kwargs):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({
                'error': 'start_date and end_date parameters are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        class_summaries = []
        class_levels = ClassLevel.objects.all()

        for class_level in class_levels:
            StudentProfile = get_student_profile_model()
            students = StudentProfile.objects.filter(class_level=class_level)
            if not students.exists():
                continue

            attendance_data = Attendance.objects.filter(
                student__in=students,
                date__range=[start_date, end_date]
            ).values('student').annotate(
                total_days=Count('id'),
                present_days=Count('id', filter=Q(status='present'))
            )

            total_students = students.count()
            if attendance_data:
                avg_attendance = sum(
                    (item['present_days'] / item['total_days'] * 100) if item['total_days'] > 0 else 0
                    for item in attendance_data
                ) / len(attendance_data)
            else:
                avg_attendance = 0

            class_summaries.append({
                'class_level': class_level.name,
                'total_students': total_students,
                'average_attendance_rate': round(avg_attendance, 2)
            })

        return Response(class_summaries, status=status.HTTP_200_OK)


# ========== BULK OPERATIONS ==========

class BulkDailyReportView(APIView):
    """Create multiple daily reports at once"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, *args, **kwargs):
        serializer = BulkDailyReportSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            reports = serializer.save()
            response_data = DailyReportSerializer(reports, many=True).data
            return Response({
                'message': f'Successfully created {len(reports)} daily reports',
                'reports': response_data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportExportView(APIView):
    """Export reports in various formats"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, *args, **kwargs):
        serializer = ReportExportSerializer(data=request.data)
        if serializer.is_valid():
            # This would typically generate and return a file
            # For now, return success message
            return Response({
                'message': 'Export request processed successfully',
                'export_type': serializer.validated_data['report_type'],
                'format': serializer.validated_data['format']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
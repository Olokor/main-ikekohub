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
    Subject, ClassLevel, Attendance, DailyReport, DailySubjectReport,
    WeeklyReport, WeeklySubjectSummary, TermReport, TermSubjectReport
)
from .serializer import (
    SubjectSerializer, ClassLevelSerializer, AttendanceSerializer,
    AttendanceBulkSerializer, AttendanceReportSerializer,
    DailyReportSerializer, DailySubjectReportSerializer,
    WeeklyReportSerializer, WeeklySubjectSummarySerializer,
    TermReportSerializer, TermSubjectReportSerializer,
    StudentAttendanceSummarySerializer, ClassAttendanceSummarySerializer,
    StudentProgressSummarySerializer, ReportingDashboardSerializer,
    BulkDailyReportSerializer, ReportExportSerializer
)


# Use apps.get_model to avoid circular imports
def get_student_profile_model():
    return apps.get_model('student_app', 'StudentProfile')


def get_teacher_profile_model():
    return apps.get_model('teacher_app', 'TeacherProfile')


# ========== SUBJECT & CLASS LEVEL VIEWS ==========

class SubjectListCreateView(generics.ListCreateAPIView):
    """List all subjects or create a new subject"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = Subject.objects.all()
        class_level = self.request.query_params.get('class_level', None)
        if class_level:
            queryset = queryset.filter(class_levels__contains=[class_level])
        return queryset.order_by('name')


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a subject"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsSchoolAdmin]


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



class AttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete an attendance record"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]


class BulkAttendanceView(APIView):
    """Mark attendance for multiple students at once"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, *args, **kwargs):
        serializer = AttendanceBulkSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            attendance_records = serializer.save()
            response_data = AttendanceSerializer(attendance_records, many=True).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendanceReportView(APIView):
    """Generate attendance reports"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, *args, **kwargs):
        serializer = AttendanceReportSerializer(data=request.data)
        if serializer.is_valid():
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            student_id = serializer.validated_data.get('student_id')
            class_level = serializer.validated_data.get('class_level')

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
                absent_days=Count('id', filter=Q(status='absent')),
                late_days=Count('id', filter=Q(status='late'))
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
                    'late_days': item['late_days'],
                    'attendance_rate': round(attendance_rate, 2)
                })

            return Response({
                'period': f"{start_date} to {end_date}",
                'total_records': queryset.count(),
                'students_summary': report_data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        if hasattr(self.request.user, 'teacher_profile'):
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=self.request.user.teacher_profile)

        return queryset.order_by('-date', 'student__user__first_name')


class DailyReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a daily report"""
    queryset = DailyReport.objects.all()
    serializer_class = DailyReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = DailyReport.objects.all()
        # Teachers can only access their own reports
        if hasattr(self.request.user, 'teacher_profile'):
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=self.request.user.teacher_profile)
        return queryset


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


class SendDailyReportToParentView(APIView):
    """Send daily report to parent"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, report_id, *args, **kwargs):
        try:
            report = DailyReport.objects.get(id=report_id)

            # Check permissions
            if hasattr(request.user, 'teacher_profile'):
                if not hasattr(request.user, 'admin_profile'):
                    if report.teacher != request.user.teacher_profile:
                        return Response({
                            'error': 'You can only send your own reports'
                        }, status=status.HTTP_403_FORBIDDEN)

            # Mark as sent
            report.sent_to_parent = True
            report.sent_at = timezone.now()
            report.save()

            # Here you would typically send an email or notification to parents
            # For now, we'll just return success

            return Response({
                'message': 'Daily report sent to parent successfully',
                'sent_at': report.sent_at
            }, status=status.HTTP_200_OK)

        except DailyReport.DoesNotExist:
            return Response({
                'error': 'Daily report not found'
            }, status=status.HTTP_404_NOT_FOUND)


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
        if hasattr(self.request.user, 'teacher_profile'):
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=self.request.user.teacher_profile)

        return queryset.order_by('-week_start_date', 'student__user__first_name')


class WeeklyReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a weekly report"""
    queryset = WeeklyReport.objects.all()
    serializer_class = WeeklyReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = WeeklyReport.objects.all()
        # Teachers can only access their own reports
        if hasattr(self.request.user, 'teacher_profile'):
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=self.request.user.teacher_profile)
        return queryset


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

        # Filter by teacher (if teacher is making request)
        if hasattr(self.request.user, 'teacher_profile'):
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=self.request.user.teacher_profile)

        return queryset.order_by('-academic_year', 'term', 'student__user__first_name')


class TermReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a term report"""
    queryset = TermReport.objects.all()
    serializer_class = TermReportSerializer
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get_queryset(self):
        queryset = TermReport.objects.all()
        # Teachers can only access their own reports
        if hasattr(self.request.user, 'teacher_profile'):
            if not hasattr(self.request.user, 'admin_profile'):
                queryset = queryset.filter(teacher=self.request.user.teacher_profile)
        return queryset


class FinalizeTermReportView(APIView):
    """Finalize a term report (prevent further editing)"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def post(self, request, report_id, *args, **kwargs):
        try:
            report = TermReport.objects.get(id=report_id)

            # Check permissions
            if hasattr(request.user, 'teacher_profile'):
                if not hasattr(request.user, 'admin_profile'):
                    if report.teacher != request.user.teacher_profile:
                        return Response({
                            'error': 'You can only finalize your own reports'
                        }, status=status.HTTP_403_FORBIDDEN)

            # Check if report has subject reports
            if not report.subject_reports.exists():
                return Response({
                    'error': 'Cannot finalize report without subject reports'
                }, status=status.HTTP_400_BAD_REQUEST)

            report.finalized = True
            report.finalized_at = timezone.now()
            report.save()

            return Response({
                'message': 'Term report finalized successfully',
                'finalized_at': report.finalized_at
            }, status=status.HTTP_200_OK)

        except TermReport.DoesNotExist:
            return Response({
                'error': 'Term report not found'
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
        if hasattr(request.user, 'teacher_profile'):
            if not hasattr(request.user, 'admin_profile'):
                recent_daily_reports = recent_daily_reports.filter(
                    teacher=request.user.teacher_profile
                )

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
                        'grade': subject_report.grade,
                        'rubric': subject_report.overall_rubric
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


class ClassPerformanceAnalyticsView(APIView):
    """Get class performance analytics"""
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]

    def get(self, request, class_level_id, *args, **kwargs):
        try:
            class_level = ClassLevel.objects.get(id=class_level_id)
            StudentProfile = get_student_profile_model()
            students = StudentProfile.objects.filter(class_level=class_level)

            academic_year = request.query_params.get('academic_year',
                                                     f"{timezone.now().year}-{timezone.now().year + 1}")
            term = request.query_params.get('term', 'first')

            # Get term reports for the class
            term_reports = TermReport.objects.filter(
                student__in=students,
                academic_year=academic_year,
                term=term
            )

            # Calculate class averages
            class_stats = {
                'total_students': students.count(),
                'reports_completed': term_reports.count(),
                'class_average': 0,
                'subject_averages': {},
                'grade_distribution': {},
                'attendance_summary': {}
            }

            if term_reports.exists():
                # Overall class average
                all_subject_reports = TermSubjectReport.objects.filter(
                    term_report__in=term_reports
                )

                if all_subject_reports.exists():
                    class_average = all_subject_reports.aggregate(
                        avg_score=Avg('total_score')
                    )['avg_score']
                    class_stats['class_average'] = round(float(class_average), 2) if class_average else 0

                    # Subject averages
                    subjects = Subject.objects.filter(
                        termsubjectreport__term_report__in=term_reports
                    ).distinct()

                    for subject in subjects:
                        subject_reports = all_subject_reports.filter(subject=subject)
                        subject_avg = subject_reports.aggregate(
                            avg_score=Avg('total_score')
                        )['avg_score']
                        class_stats['subject_averages'][subject.name] = round(
                            float(subject_avg), 2
                        ) if subject_avg else 0

                    # Grade distribution
                    grade_counts = all_subject_reports.values('grade').annotate(
                        count=Count('grade')
                    )
                    for grade_data in grade_counts:
                        grade = grade_data['grade']
                        count = grade_data['count']
                        class_stats['grade_distribution'][grade] = count

            # Attendance summary for the class
            class_attendance = Attendance.objects.filter(student__in=students)
            if class_attendance.exists():
                total_records = class_attendance.count()
                present_records = class_attendance.filter(status='present').count()
                attendance_rate = (present_records / total_records * 100) if total_records > 0 else 0

                class_stats['attendance_summary'] = {
                    'total_records': total_records,
                    'present_records': present_records,
                    'attendance_rate': round(attendance_rate, 2)
                }

            return Response({
                'class_level': {
                    'id': class_level.id,
                    'name': class_level.name,
                    'is_toddler_class': class_level.is_toddler_class
                },
                'academic_period': {
                    'academic_year': academic_year,
                    'term': term
                },
                'statistics': class_stats
            }, status=status.HTTP_200_OK)

        except ClassLevel.DoesNotExist:
            return Response({
                'error': 'Class level not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ========== PARENT ACCESS VIEWS ==========

class ParentStudentReportsView(APIView):
    """Get reports for parent's children"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Check if user is a parent
        if not hasattr(request.user, 'parent_profile'):
            return Response({
                'error': 'Access denied. Parent account required.'
            }, status=status.HTTP_403_FORBIDDEN)

        parent = request.user.parent_profile
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
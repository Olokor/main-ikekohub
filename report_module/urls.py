# report_module/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ========== SUBJECT & CLASS LEVEL ENDPOINTS ==========
    path('subjects/', views.SubjectListCreateView.as_view(), name='subject-list-create'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),
    path('class-levels/', views.ClassLevelListCreateView.as_view(), name='class-level-list-create'),
    path('class-levels/<int:pk>/', views.ClassLevelDetailView.as_view(), name='class-level-detail'),

    # ========== ATTENDANCE ENDPOINTS ==========
    path('attendance/', views.AttendanceListCreateView.as_view(), name='attendance-list-create'),
    path('attendance/<int:pk>/', views.AttendanceDetailView.as_view(), name='attendance-detail'),
    path('attendance/bulk/', views.BulkAttendanceView.as_view(), name='attendance-bulk'),
    path('attendance/report/', views.AttendanceReportView.as_view(), name='attendance-report'),
    path('attendance/class-summary/', views.ClassAttendanceSummaryView.as_view(), name='class-attendance-summary'),

    # ========== DAILY REPORT ENDPOINTS ==========
    path('daily-reports/', views.DailyReportListCreateView.as_view(), name='daily-report-list-create'),
    path('daily-reports/<int:pk>/', views.DailyReportDetailView.as_view(), name='daily-report-detail'),
    path('daily-reports/bulk/', views.BulkDailyReportView.as_view(), name='daily-report-bulk'),
    path('daily-reports/<int:report_id>/send-to-parent/', views.SendDailyReportToParentView.as_view(),
         name='send-daily-report'),

    # ========== WEEKLY REPORT ENDPOINTS ==========
    path('weekly-reports/', views.WeeklyReportListCreateView.as_view(), name='weekly-report-list-create'),
    path('weekly-reports/<int:pk>/', views.WeeklyReportDetailView.as_view(), name='weekly-report-detail'),

    # ========== TERM REPORT ENDPOINTS ==========
    path('term-reports/', views.TermReportListCreateView.as_view(), name='term-report-list-create'),
    path('term-reports/<int:pk>/', views.TermReportDetailView.as_view(), name='term-report-detail'),
    path('term-reports/<int:report_id>/finalize/', views.FinalizeTermReportView.as_view(), name='finalize-term-report'),

    # ========== DASHBOARD & ANALYTICS ENDPOINTS ==========
    path('dashboard/', views.ReportingDashboardView.as_view(), name='reporting-dashboard'),
    path('analytics/student/<int:student_id>/', views.StudentProgressAnalyticsView.as_view(), name='student-analytics'),
    path('analytics/class/<int:class_level_id>/', views.ClassPerformanceAnalyticsView.as_view(),
         name='class-analytics'),

    # ========== PARENT ACCESS ENDPOINTS ==========
    path('parent/reports/', views.ParentStudentReportsView.as_view(), name='parent-student-reports'),
]
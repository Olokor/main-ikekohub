# report_module/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ========== SUBJECT & TOPIC ENDPOINTS ==========
    path('subjects/', views.SubjectListCreateView.as_view(), name='subject-list-create'),
    path('subjects/<int:pk>/', views.SubjectDetailView.as_view(), name='subject-detail'),
    path('topics/', views.TopicListCreateView.as_view(), name='topic-list-create'),
    path('topics/<int:pk>/', views.TopicDetailView.as_view(), name='topic-detail'),

    # ========== DEPARTMENT ENDPOINTS ==========
    path('departments/', views.DepartmentListCreateView.as_view(), name='department-list-create'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department-detail'),

    # ========== CLASS LEVEL ENDPOINTS ==========
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
    path('daily-reports/sub-subject/', views.DailySubSubjectReportListCreateView.as_view(),
         name='daily-sub-subject-list-create'),

    # ========== WEEKLY REPORT ENDPOINTS ==========
    path('weekly-reports/', views.WeeklyReportListCreateView.as_view(), name='weekly-report-list-create'),
    path('weekly-reports/<int:pk>/', views.WeeklyReportDetailView.as_view(), name='weekly-report-detail'),
    path('weekly-reports/sub-subject/', views.WeeklySubSubjectSummaryListCreateView.as_view(),
         name='weekly-sub-subject-list-create'),

    # ========== TERM REPORT ENDPOINTS ==========
    path('term-reports/', views.TermReportListCreateView.as_view(), name='term-report-list-create'),
    path('term-reports/<int:pk>/', views.TermReportDetailView.as_view(), name='term-report-detail'),
    path('term-reports/<int:report_id>/finalize/', views.FinalizeTermReportView.as_view(), name='finalize-term-report'),
    path('term-reports/subjects/', views.TermSubjectReportListCreateView.as_view(),
         name='term-subject-report-list-create'),
    path('term-reports/sub-subject-assessments/', views.TermSubSubjectAssessmentListCreateView.as_view(),
         name='term-sub-subject-assessment-list-create'),

    # ========== LEARNING GOALS ENDPOINTS ==========
    path('learning-goals/', views.LearningGoalListCreateView.as_view(), name='learning-goal-list-create'),
    path('learning-goals/<int:pk>/', views.LearningGoalDetailView.as_view(), name='learning-goal-detail'),
    path('learning-goals/progress/', views.StudentLearningGoalProgressListCreateView.as_view(),
         name='student-goal-progress-list-create'),
    path('learning-goals/progress/<int:pk>/', views.StudentLearningGoalProgressDetailView.as_view(),
         name='student-goal-progress-detail'),

    # ========== REPORT APPROVAL ENDPOINTS ==========
    path('approvals/', views.ReportApprovalListView.as_view(), name='report-approval-list'),
    path('approvals/<int:approval_id>/approve/', views.ApproveReportView.as_view(), name='approve-report'),

    # ========== DASHBOARD & ANALYTICS ENDPOINTS ==========
    path('dashboard/', views.ReportingDashboardView.as_view(), name='reporting-dashboard'),
    path('analytics/student/<int:student_id>/', views.StudentProgressAnalyticsView.as_view(), name='student-analytics'),

    # ========== PARENT ACCESS ENDPOINTS ==========
    path('parent/reports/', views.ParentStudentReportsView.as_view(), name='parent-student-reports'),
    path('parent/feedback/', views.ParentFeedbackListCreateView.as_view(), name='parent-feedback-list-create'),
    path('parent/feedback/<int:pk>/', views.ParentFeedbackDetailView.as_view(), name='parent-feedback-detail'),
    path('parent/feedback/<int:feedback_id>/respond/', views.RespondToParentFeedbackView.as_view(),
         name='respond-to-feedback'),

    # ========== NOTIFICATION ENDPOINTS ==========
    path('notifications/', views.ReportNotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', views.MarkNotificationReadView.as_view(),
         name='mark-notification-read'),

    # ========== ACADEMIC YEAR & SETTINGS ENDPOINTS ==========
    path('academic-years/', views.AcademicYearListCreateView.as_view(), name='academic-year-list-create'),
    path('academic-years/<int:pk>/', views.AcademicYearDetailView.as_view(), name='academic-year-detail'),
    path('academic-years/<int:year_id>/set-current/', views.SetCurrentAcademicYearView.as_view(),
         name='set-current-year'),
    path('settings/', views.ReportSettingsView.as_view(), name='report-settings'),

    # ========== TEMPLATE ENDPOINTS ==========
    path('templates/', views.ReportTemplateListCreateView.as_view(), name='template-list-create'),
    path('templates/<int:pk>/', views.ReportTemplateDetailView.as_view(), name='template-detail'),

    # ========== EXPORT ENDPOINTS ==========
    path('export/', views.ReportExportView.as_view(), name='report-export'),
]
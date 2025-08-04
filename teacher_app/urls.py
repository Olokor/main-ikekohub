from django.urls import include, path

from teacher_app.views import TeacherDashboardView

urlpatterns = [
    path("teacher-dashboard/", TeacherDashboardView.as_view(), name="teacher"),
]
from django.urls import include, path

from teacher_app.views import CreateTeacherView, TeacherDashboardView

urlpatterns = [
    path("create-teacher/", CreateTeacherView.as_view(), name="create-teacher"),
    path("teacher-dashboard/", TeacherDashboardView.as_view(), name="teacher"),
]
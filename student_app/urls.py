from django.urls import include, path

from student_app.views import StudentDashBoardView
urlpatterns = [
    path("student-dashboard/", StudentDashBoardView.as_view(), name="student-dashboard"),
    # path("create-student/", CreateStudentView.as_view(), name="create-student"),
]
from django.urls import include, path
from . import views
from rest_framework import generics
urlpatterns = [
    path('create-admin/', views.CreateAdminUser.as_view(), name='create-admin'),
    path('create-teacher/', views.CreateTeacherView.as_view(), name='create-teacher'),
    path('create-student/', views.CreateStudentView.as_view(), name='create-student'),
    path('create-students/', views.CreateBulkStudent.as_view(), name='create-students'),
    path('get-teacher/<str:username>', views.GetTeacherByUsername.as_view(), name='get-teacher'),
    path('get-all-teachers', views.GetAllTeachers.as_view(), name='get-all-teachers'),
    path('get-student/<str:admission_number>', views.GetStudentByAdmissionNumber.as_view(), name='get-student'),
    path('get-all-student/', views.GetAllStudents.as_view(), name='get-all-students'),
    path('update-student/<int:pk>', views.UpdateStudentCredential.as_view(), name='update-student'),
    path('update-teacher/<int:pk>', views.UpdateTeacherCredential.as_view(), name='update-teacher'),
    path('delete-student/<int:pk>', views.DeleteStudentCredential.as_view(), name='delete-student'),
    path('delete-teacher/<int:pk>', views.DeleteTeacherCredential.as_view(), name='delete-teacher'),
]
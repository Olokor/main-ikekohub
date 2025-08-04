from django.urls import include, path
from . import views
urlpatterns = [
    path('create-admin/', views.CreateAdminUser.as_view(), name='create-admin'),
    path('create-teacher/', views.CreateTeacherView.as_view(), name='create-teacher'),
    path('create-student/', views.CreateStudentView.as_view(), name='create-student'),
    path('create-students/', views.CreateBulkStudent.as_view(), name='create-students'),
]
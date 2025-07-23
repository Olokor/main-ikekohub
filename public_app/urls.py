from django.urls import path

from . import views

urlpatterns = [
    path('create-school/', views.CreateSchoolView.as_view(), name='create-school'),
]
from django.urls import include, path
from . import views
urlpatterns = [
    path('create-admin/', views.CreateAdminUser.as_view(), name='create-admin'),
]
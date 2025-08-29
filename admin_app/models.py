# admin_app/models.py
from django.db import models
from public_app.models import TenantUser


class AdminProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        TEACHER = 'teacher'
        PARENT = 'parent'
        STUDENT = 'student'

    user = models.OneToOneField(TenantUser, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ADMIN)

    def __str__(self):
        return f"{self.role}"

# Remove these models - they're now in report_module
# class ClassLevel(models.Model):
#     pass

# class Subject(models.Model):
#     pass
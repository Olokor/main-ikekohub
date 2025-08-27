from django.db import models

from public_app.models import TenantUser


# Create your models here.
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

class ClassLevel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.name}"
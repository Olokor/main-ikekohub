from django.db import models

from public_app.models import TenantUser
from student_app.models import StudentProfile


# Create your models here.
class ParentProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        TEACHER = 'teacher'
        PARENT = 'parent'
        STUDENT = 'student'
    user = models.OneToOneField(TenantUser, on_delete=models.CASCADE, related_name='parent_profile')
    children = models.ManyToManyField(StudentProfile, related_name='parents')
    occupation = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PARENT)


    def __str__(self):
        return f"{self.user.username} {self.role}"
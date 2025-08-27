from django.db import models

from admin_app.models import ClassLevel
from public_app.models import TenantUser


class TeacherProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        TEACHER = 'teacher'
        PARENT = 'parent'
        STUDENT = 'student'

    user = models.OneToOneField(TenantUser, on_delete=models.CASCADE, related_name='teacher_profile')
    subject_taught = models.JSONField(default=list)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name='teacher_class', blank=True, null=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.TEACHER)



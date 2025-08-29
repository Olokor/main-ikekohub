# teacher_app/models.py
from django.db import models
from public_app.models import TenantUser

class TeacherProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        TEACHER = 'teacher'
        PARENT = 'parent'
        STUDENT = 'student'

    user = models.OneToOneField(TenantUser, on_delete=models.CASCADE, related_name='teacher_profile')
    subject_taught = models.JSONField(default=list)
    # Use string reference to avoid circular import
    class_level = models.ForeignKey('report_module.ClassLevel', on_delete=models.CASCADE, 
                                   related_name='teacher_class', blank=True, null=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.TEACHER)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
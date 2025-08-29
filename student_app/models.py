# student_app/models.py
from django.db import models
from public_app.models import TenantUser


class StudentProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin'
        TEACHER = 'teacher'
        PARENT = 'parent'
        STUDENT = 'student'

    user = models.OneToOneField(TenantUser, on_delete=models.CASCADE, related_name='student_profile')
    admission_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    parent_name = models.CharField(max_length=100)
    parent_contact = models.CharField(max_length=20)
    parent_email = models.CharField(max_length=100)
    address = models.TextField()
    # Use string reference to avoid circular import
    class_level = models.ForeignKey('report_module.ClassLevel', on_delete=models.CASCADE,
                                    related_name='student_class', blank=True, null=True)
    academic_year = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='student_profiles/', blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)

    def __str__(self):
        return f"{self.user.username} {self.role}"
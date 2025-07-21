from django.db import models

from public_app.models import TenantUser


# Create your models here.
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
    class_level = models.CharField(max_length=50)
    academic_year = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='student_profiles/', blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)

    def __str__(self):
        return f"{self.user.username} {self.user.role}"

    def __str__(self):
        return f"{self.user.username} {self.user.role}"

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.functions.text import Lower
from django_tenants.models import DomainMixin, TenantMixin
# Create your models here.

class School(TenantMixin):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    admin_email = models.EmailField(blank=True)
    admin_first_name = models.CharField(max_length=30,blank=True)
    admin_last_name = models.CharField(max_length=30, blank=True)

    auto_create_schema = True

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new and self.name !="Public":
            self.create_tenant_admin()

    def create_tenant_admin(self):
        from django_tenants.utils import tenant_context
        from admin_app.models import  AdminProfile
        # Use tenant context to create objects in the tenant schema
        with tenant_context(self):
            # Create the admin user
            admin_user = TenantUser.objects.create(
                username=self.admin_email,
                email=self.admin_email,
                first_name=self.admin_first_name,
                last_name=self.admin_last_name,
                is_active=True,
                is_staff=True,
                school=self,
            )

            # Set password (you might want to generate a random one and email it)
            admin_user.password = make_password('Default_password12345!')
            admin_user.save()

            # Create the admin profile and role
            AdminProfile.objects.create(user=admin_user)

            # You might want to send an email with credentials here

class Domain(DomainMixin):
    pass

class TenantUser(AbstractUser):
    is_verified = models.BooleanField(default=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, blank=True, null=True)
    username = models.CharField(max_length=255, unique=False)
    email = models.EmailField(max_length=255, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['school']),
        ]
        constraints = [
            # Case-insensitive uniqueness
            models.UniqueConstraint(
                Lower('email'),
                name='tenantuser_email_lower_unique',
            ),
        ]

    def clean(self):
        """Validation for case-insensitive email uniqueness"""
        super().clean()
        if TenantUser.objects.filter(email__iexact=self.email).exclude(pk=self.pk).exists():
            raise ValidationError({'email': 'A user with this email already exists.'})

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Override save method with transaction and validation"""
        self.full_clean()  # Runs clean() method validation
        super().save(*args, **kwargs)

    def validate_unique(self, exclude=None):
        """Additional validation for uniqueness"""
        super().validate_unique(exclude)
        qs = TenantUser.objects.filter(email__iexact=self.email)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError({'email': 'This email is already in use.'})

    def __str__(self):
        return self.username


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from parent_app.models import ParentProfile
from student_app.models import StudentProfile
from django_tenants.utils import tenant_context


@receiver(post_save, sender=StudentProfile)
def handle_parent_creation(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        school = instance.user.school  # Ensure this exists
        with tenant_context(school):
            TenantUser = get_user_model()

            username_base = instance.parent_email.split('@')[0]
            username = f"parent_{username_base[:15]}"

            parent_user, user_created = TenantUser.objects.get_or_create(
                email=instance.parent_email,
                defaults={
                    'username': username,
                    'school': school,
                    'password':f"Parent{instance.admission_number}!",
                    'first_name': instance.parent_name.split()[0],
                    'last_name': ' '.join(instance.parent_name.split()[1:]) if ' ' in instance.parent_name else '',
                }
            )
            parent_user.save()
            print(f"Created parent user: {parent_user}, user_created: {user_created}")

            # if user_created:
            #     parent_user.set_password(f"Parent{instance.admission_number}!")
            #     parent_user.save()
            #     print(f"password set for parent user: {parent_user}")
            parent_profile, _ = ParentProfile.objects.get_or_create(
                user=parent_user,
                defaults={'occupation': ''}
            )
            parent_profile.save()
            print(f"Created parent profile: {parent_profile}")
            if not parent_profile.children.filter(id=instance.id).exists():
                parent_profile.children.add(instance)

    except Exception as e:
        print(f"Error in parent creation signal: {e}")

from rest_framework import serializers

from public_app.models import TenantUser, School
from student_app.models import StudentProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(write_only=True, required=True)
    last_name = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    school = serializers.CharField(write_only=True, required=True)
    parent_email = serializers.EmailField(required=True)
    parent_name = serializers.CharField(required=True, max_length=100)
    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'username', 'email', 'password', 'school',
            'admission_number', 'date_of_birth', 'parent_name',
            'parent_email', 'address', 'parent_contact',
            'class_level', 'academic_year', 'first_name', 'last_name'
        ]
        read_only_fields = ['id', 'user']

    def validate(self, data):
        if not School.objects.filter(name=data['school']).exists():
            raise serializers.ValidationError({
                'school': f"School '{data['school']}' does not exist."
            })
        return data

    def create(self, validated_data):
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'password': validated_data['password'],
            'school': School.objects.get(name=validated_data['school'])
        }

        user = TenantUser.objects.create_user(**user_data)
        student_profile = StudentProfile.objects.create(
            user=user,
            admission_number=validated_data['admission_number'],
            date_of_birth=validated_data['date_of_birth'],
            parent_name=validated_data['parent_name'],
            parent_email=validated_data['parent_email'],
            address=validated_data['address'],
            parent_contact=validated_data['parent_contact'],
            class_level=validated_data['class_level'],
            academic_year=validated_data['academic_year'],
        )

        return {
            'id': student_profile.id,
            'username': user.username,
            'email': user.email,
            'school': validated_data['school'],
            'admission_number': validated_data['admission_number'],
            'date_of_birth': validated_data['date_of_birth'],
            'parent_name': validated_data['parent_name'],
            'parent_email': validated_data['parent_email'],
            'address': validated_data['address'],
            'parent_contact': validated_data['parent_contact'],
            'class_level': validated_data['class_level'],
            'academic_year': validated_data['academic_year'],
            'parent_username': student_profile.parents.first().user.username if student_profile.parents.exists() else None
        }


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    # Optional user-related fields for nested updates
    username = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    school = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'username', 'email', 'password', 'school',
            'admission_number', 'date_of_birth', 'parent_name',
            'parent_email', 'address', 'parent_contact',
            'class_level', 'academic_year', 'first_name', 'last_name'
        ]
        read_only_fields = ['id', 'user']

    def validate(self, data):
        # Only validate school if it's being updated
        if 'school' in data and not School.objects.filter(name=data['school']).exists():
            raise serializers.ValidationError({
                'school': f"School '{data['school']}' does not exist."
            })
        return data

    def update(self, instance, validated_data):
        # Handle nested user update
        user = instance.user
        user_fields = ['username', 'first_name', 'last_name', 'email', 'password']

        for field in user_fields:
            if field in validated_data:
                if field == 'password':
                    user.set_password(validated_data[field])
                else:
                    setattr(user, field, validated_data[field])
        user.save()

        # Handle school update
        if 'school' in validated_data:
            user.school = School.objects.get(name=validated_data['school'])
            user.save()

        # Update StudentProfile fields
        profile_fields = [
            'admission_number', 'date_of_birth', 'parent_name', 'parent_email',
            'address', 'parent_contact', 'class_level', 'academic_year'
        ]
        for field in profile_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        instance.save()
        return instance

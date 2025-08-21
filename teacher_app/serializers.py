from rest_framework import serializers

from public_app.models import School, TenantUser
from teacher_app.models import TeacherProfile


class TeacherProfileCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    school = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = TeacherProfile
        fields = [
            'username', 'email', 'password', 'school',
             # Add other teacher profile fields
        ]

    def validate(self, data):
        # Check if school exists
        if not School.objects.filter(name=data['school']).exists():
            raise serializers.ValidationError({
                'school': f"School '{data['school']}' does not exist."
            })
        return data

    def create(self, validated_data):
        # Extract user creation data
        user_data = {
            'username': validated_data['username'],
            'email': validated_data['email'],
            'password': validated_data['password'],
            'school': School.objects.get(name=validated_data['school'])
        }

        # Create user
        user = TenantUser.objects.create_user(**user_data)

        # Create teacher profile
        teacher_profile = TeacherProfile.objects.create(
            user=user
        )
        return {
            'id': teacher_profile.id,
            'username': user.username,
            'email': user.email,
            'school': validated_data['school']
        }

class TeacherProfileDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    school = serializers.CharField(source='user.school.name')

    class Meta:
        model = TeacherProfile
        fields = ['id', 'username', 'email', 'school']


class TeacherProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    school = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'user', 'username', 'email', 'password', 'school',
            'subject_taught', 'first_name', 'last_name'
        ]
        read_only_fields = ['id', 'user']

    def validate(self, data):
        # Validate school only if provided
        if 'school' in data and not School.objects.filter(name=data['school']).exists():
            raise serializers.ValidationError({
                'school': f"School '{data['school']}' does not exist."
            })
        return data

    def update(self, instance, validated_data):
        user = instance.user

        # Update user fields if present
        user_fields = ['username', 'first_name', 'last_name', 'email', 'password']
        for field in user_fields:
            if field in validated_data:
                if field == 'password':
                    user.set_password(validated_data[field])
                else:
                    setattr(user, field, validated_data[field])
        user.save()

        # Update school if present
        if 'school' in validated_data:
            user.school = School.objects.get(name=validated_data['school'])
            user.save()

        # Update TeacherProfile fields
        if 'subject_taught' in validated_data:
            instance.subject_taught = validated_data['subject_taught']

        instance.save()
        return instance
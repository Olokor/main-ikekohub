from rest_framework import serializers

from admin_app.models import AdminProfile
from public_app.models import TenantUser, School


class AdminProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    school = serializers.CharField(write_only=True, required=True)
    is_staff = serializers.BooleanField(read_only=True, default=False)
    department = serializers.CharField(write_only=True, required=True)



    class Meta:
        model = AdminProfile
        fields = [
            'username', 'email', 'password', 'school','department','is_staff'
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
            'school': School.objects.get(name=validated_data['school']),
            # 'is_staff': validated_data['is_staff']
        }

        # Create user
        user = TenantUser.objects.create_user(**user_data)


        admin_profile = AdminProfile.objects.create(
            user=user,
            department=validated_data['department']
        )
        return {
            'id': admin_profile.id,
            'username': user.username,
            'email': user.email,
            'school': validated_data['school']
        }
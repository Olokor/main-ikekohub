from rest_framework import serializers, generics

from public_app.models import School, Domain, TenantUser


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'

class SchoolDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = '__all__'
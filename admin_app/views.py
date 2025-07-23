from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response

from admin_app.permission import IsSchoolAdmin
from admin_app.serializer import AdminProfileSerializer


# Create your views here.
class CreateAdminUser(generics.CreateAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = AdminProfileSerializer

    def create(self, request, *args, **kwargs):
        serializer = AdminProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin_user = serializer.save()
        return Response(admin_user, status=201)

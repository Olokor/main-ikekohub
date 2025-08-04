from django.shortcuts import render
from rest_framework import generics, status
from admin_app.permission import IsSchoolAdmin
from teacher_app.permission import IsTeacher
from teacher_app.serializers import TeacherProfileCreateSerializer
from rest_framework.response import Response

# Create your views here.


class TeacherDashboardView(generics.GenericAPIView):
    permission_classes = [IsTeacher]
    def get(self, request, *args, **kwargs):
        return Response({
            "message": "Teacher Dashboard",
        })
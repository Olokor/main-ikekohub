from django.shortcuts import render

from admin_app.permission import IsSchoolAdmin
from student_app.permission import IsStudent
from student_app.serializers import StudentProfileSerializer
from rest_framework.response import Response
from rest_framework import generics, status

# Create your views here.

class StudentDashBoardView(generics.RetrieveAPIView):
    permission_classes = [IsStudent, IsSchoolAdmin]
    def get(self):
        return Response({
            "message": "Student dashboard",
        })
from django.shortcuts import render
from rest_framework import generics, status
from admin_app.permission import IsSchoolAdmin
from teacher_app.permission import IsTeacher
from teacher_app.serializers import TeacherProfileCreateSerializer
from rest_framework.response import Response

# Create your views here.
class CreateTeacherView(generics.CreateAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = TeacherProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        teacher_data = serializer.save()
        return Response(teacher_data, status=status.HTTP_201_CREATED)


class TeacherDashboardView(generics.GenericAPIView):
    permission_classes = [IsTeacher]
    def get(self, request, *args, **kwargs):
        return Response({
            "message": "Teacher Dashboard",
        })
from rest_framework import generics,status
from rest_framework.response import Response

from admin_app.permission import IsSchoolAdmin
from admin_app.serializer import AdminProfileSerializer
from student_app.serializers import StudentProfileCreateSerializer
from teacher_app.serializers import TeacherProfileCreateSerializer


# Create your views here.
class CreateAdminUser(generics.CreateAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = AdminProfileSerializer

    def create(self, request, *args, **kwargs):
        serializer = AdminProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin_user = serializer.save()
        return Response(admin_user, status=201)

class CreateTeacherView(generics.CreateAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = TeacherProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        teacher_data = serializer.save()
        return Response(teacher_data, status=status.HTTP_201_CREATED)

class CreateStudentView(generics.CreateAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = StudentProfileCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_data = serializer.save()
        return Response(student_data, status=status.HTTP_201_CREATED)

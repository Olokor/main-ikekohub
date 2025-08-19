from django.shortcuts import get_object_or_404
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from admin_app.permission import IsSchoolAdmin
from admin_app.serializer import AdminProfileSerializer
from student_app.serializers import StudentProfileCreateSerializer
from teacher_app.models import TeacherProfile
from teacher_app.serializers import TeacherProfileCreateSerializer, TeacherProfileDetailSerializer


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


class CreateBulkStudent(APIView):
    permission_classes = [IsSchoolAdmin]

    def post(self, request, *args, **kwargs):
        # Expecting a list of student objects in JSON array format
        students_data = request.data

        if not isinstance(students_data, list):
            return Response(
                {"error": "Expected a list of student objects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        errors = []

        for index, student_data in enumerate(students_data):
            serializer = StudentProfileCreateSerializer(data=student_data)
            if serializer.is_valid():
                student_result = serializer.save()
                results.append(student_result)
            else:
                errors.append({
                    "index": index,
                    "errors": serializer.errors,
                    "data": student_data.get("username", None)
                })

        response = {"successfully_created": results}

        if errors:
            response["errors"] = errors

        return Response(response, status=status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED)


class GetTeacherByUsername(generics.RetrieveAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = TeacherProfileDetailSerializer
    lookup_field = 'User__username'

    def get(self, request, username, *args, **kwargs):
        teacher = get_object_or_404(TeacherProfile, user__username=username)
        serializer = self.get_serializer(teacher, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetAllTeachers(generics.ListAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = TeacherProfileDetailSerializer

    def get(self, request, *args, **kwargs):
        teachers = TeacherProfile.objects.all()
        serializer = self.get_serializer(teachers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


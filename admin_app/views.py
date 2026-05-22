from django.shortcuts import get_object_or_404
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from admin_app.permission import IsSchoolAdmin, AnyOf
from admin_app.serializer import AdminProfileSerializer
from student_app.models import StudentProfile
from student_app.serializers import StudentProfileSerializer, StudentProfileUpdateSerializer
from teacher_app.models import TeacherProfile
from teacher_app.permission import IsTeacher
from teacher_app.serializers import TeacherProfileCreateSerializer, TeacherProfileDetailSerializer, \
    TeacherProfileUpdateSerializer

# Import ClassLevelSerializer from report_module
from report_module.serializer import ClassLevelSerializer
from report_module.models import ClassLevel

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
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]
    serializer_class = StudentProfileSerializer

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
            serializer = StudentProfileSerializer(data=student_data)
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

class GetStudentByAdmissionNumber(generics.RetrieveAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = StudentProfileSerializer

    def get(self, request, admission_number, *args, **kwargs):
        student = get_object_or_404(StudentProfile, admission_number=admission_number)
        serializer = self.get_serializer(student, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetAllStudents(generics.ListAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = StudentProfileSerializer

    def get(self, request, *args, **kwargs):
        students = StudentProfile.objects.all()
        serializer = self.get_serializer(students, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateStudentCredential(generics.UpdateAPIView):
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]
    serializer_class = StudentProfileUpdateSerializer
    queryset = StudentProfile.objects.all()

class UpdateTeacherCredential(generics.UpdateAPIView):
    permission_classes = [IsSchoolAdmin]
    serializer_class = TeacherProfileUpdateSerializer
    queryset = TeacherProfile.objects.all()


class DeleteStudentCredential(generics.DestroyAPIView):
    permission_classes = [AnyOf(IsSchoolAdmin, IsTeacher)]
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer


class DeleteTeacherCredential(generics.DestroyAPIView):
    permission_classes = [IsSchoolAdmin]
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileDetailSerializer


class GetAllClasses(generics.ListAPIView):
    """
    Get all classes (ClassLevel) in the system.
    Only accessible by school administrators.
    """
    permission_classes = [IsSchoolAdmin]
    serializer_class = ClassLevelSerializer
    
    def get_queryset(self):
        # Import ClassLevel from report_module
        return ClassLevel.objects.all().order_by('name')
        
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'classes': serializer.data
        }, status=status.HTTP_200_OK)


class CreateClassLevelView(generics.CreateAPIView):
    """
    Create a new class level.
    Only accessible by school administrators.
    """
    permission_classes = [IsSchoolAdmin]
    serializer_class = ClassLevelSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        class_level = serializer.save()
        return Response({
            'message': 'Class level created successfully',
            'class_level': ClassLevelSerializer(class_level).data
        }, status=status.HTTP_201_CREATED)

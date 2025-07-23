
# Create your views here.
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from public_app.models import Domain
from public_app.serializers import SchoolSerializer, SchoolDomainSerializer


class CreateSchoolView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SchoolSerializer
    def post(self, request, *args, **kwargs):
        serializer = SchoolSerializer(data=request.data)
        if serializer.is_valid():
            school = serializer.save()
            domain = Domain.objects.create(domain=f"{remove_space(school.name)}.localhost", is_primary=True, tenant=school)
            domain.save()
            domain_serializer = SchoolDomainSerializer(domain)
            school_serializer = SchoolSerializer(school)
            return Response({'school': school_serializer.data, 'domain':domain_serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def remove_space(string) -> str:
    return string.replace(' ', '')

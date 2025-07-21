# For tenant-specific schemas
from django.urls import path, include
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
schema_view = get_schema_view(
    openapi.Info(
        title="Tenant API Documentation",
        default_version='v1',
        description="Tenant-specific endpoints",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
# urls.py


urlpatterns = [
    path('api-tenant/admin', include('admin_app.urls')),
    path('api-tenant/teacher', include('teacher_app.urls')),
    path('api-tenant/student', include('student_app.urls')),
    path('api-tenant/parent', include('parent_app.urls')),
    path('api-tenant/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api-tenant/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('swagger/tenant/', schema_view.with_ui('swagger', cache_timeout=0), name='tenant-schema-swagger'),
]
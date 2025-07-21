from django.urls import path, include
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

schema_view = get_schema_view(
    openapi.Info(
        title="Public API Documentation",
        default_version='v1',
        description="Public endpoints for tenant management",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # path('api/admin/', admin.site.urls),
    path('api/public/', include('public_app.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('api/auth/password/reset/confirm/<str:uidb64>/<str:token>/', 
         PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('swagger/public/', schema_view.with_ui('swagger', cache_timeout=0), name='public-schema-swagger'),
]
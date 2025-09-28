
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger schema configuration
schema_view = get_schema_view(
   openapi.Info(
      title="Todo API",
      default_version='v1',
      description="""
API для управления задачами (Todo List)

## Аутентификация
API использует JWT токены для аутентификации. 

### Получение токена:
1. POST /api/auth/token/ - получить access и refresh токены
2. POST /api/auth/token/refresh/ - обновить access токен

### Использование токена:
Добавьте токен в заголовок Authorization: `Bearer YOUR_ACCESS_TOKEN`

### Время жизни токенов:
- Access токен: 1 час
- Refresh токен: 7 дней
      """,
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@todoapi.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('todo_proj.tasks.urls')),
    
    # JWT Authentication endpoints
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

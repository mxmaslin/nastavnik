from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from lessons import views

urlpatterns = [
    path('', views.backend_root, name='backend_root'),
    path('admin/', admin.site.urls),
    path('', include('django_prometheus.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path('api/', include('lessons.urls')),
    path('api/health/', views.health_check, name='health_check'),
]

from django.contrib import admin
from django.urls import path, include
from lessons import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django_prometheus.urls')),
    path('api/', include('lessons.urls')),
    path('api/health/', views.health_check, name='health_check'),
]

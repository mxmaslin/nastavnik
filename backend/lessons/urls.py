from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'lessons', views.LessonViewSet)
router.register(r'questions', views.QuestionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('answer/submit/', views.submit_answer, name='submit-answer'),
    path('answer/status/<uuid:interaction_id>/', views.interaction_status, name='interaction-status'),
    path('statistics/', views.statistics, name='statistics'),
]

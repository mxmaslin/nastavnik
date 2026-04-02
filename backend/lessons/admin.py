from django.contrib import admin
from .models import Lesson, Question, InteractionRecord, LessonSession


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at', 'updated_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'lesson', 'order', 'correct_answer']
    list_filter = ['lesson']
    search_fields = ['text']


@admin.register(InteractionRecord)
class InteractionRecordAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'question', 'user_answer', 'is_correct', 'ml_service_success', 'answered_at']
    list_filter = ['is_correct', 'ml_service_success', 'answered_at']
    search_fields = ['session_id', 'user_answer']
    readonly_fields = ['answered_at']


@admin.register(LessonSession)
class LessonSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'lesson', 'current_question_index', 'is_completed', 'started_at']
    list_filter = ['is_completed', 'lesson']
    search_fields = ['session_id']

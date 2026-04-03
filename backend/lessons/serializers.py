from rest_framework import serializers
from .models import Lesson, Question, InteractionRecord, LessonSession


class QuestionSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'text', 'order', 'choices']
        read_only_fields = ['id', 'choices']

    def get_choices(self, obj):
        return obj.shuffled_choices()


class LessonSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'text', 'questions', 'created_at']
        read_only_fields = ['id', 'created_at']


class LessonListSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'question_count', 'created_at']

    def get_question_count(self, obj):
        return obj.questions.count()


class InteractionRecordSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)

    class Meta:
        model = InteractionRecord
        fields = [
            'id', 'session_id', 'question', 'question_text',
            'user_answer', 'is_correct', 'ml_service_success',
            'response_time', 'answered_at'
        ]
        read_only_fields = ['id', 'answered_at']


class LessonSessionSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    success_rate = serializers.ReadOnlyField()

    class Meta:
        model = LessonSession
        fields = [
            'id', 'session_id', 'lesson', 'lesson_title',
            'current_question_index', 'started_at', 'completed_at',
            'is_completed', 'success_rate'
        ]
        read_only_fields = ['id', 'started_at']


class AnswerSubmitSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=255)
    question_id = serializers.UUIDField()
    answer = serializers.CharField(max_length=255, allow_blank=True)


class StatisticsSerializer(serializers.Serializer):
    total_sessions = serializers.IntegerField(
        help_text='Число строк LessonSession в выборке (обычно уникальные пары session_id+урок).',
    )
    completed_sessions = serializers.IntegerField(
        help_text=(
            'Без attempt_number: сумма completion_count по LessonSession в выборке. '
            'С attempt_number (scope=attempt): 1, если по этой попытке закрыты все вопросы урока, иначе 0.'
        ),
    )
    total_questions_answered = serializers.IntegerField(
        help_text='Число записей InteractionRecord в выборке (все попытки/ответы, включая таймауты и автозапись при завершении).',
    )
    correct_answers = serializers.IntegerField(
        help_text='Записи с is_correct=true.',
    )
    success_rate = serializers.FloatField(
        help_text='Доля верных от total_questions_answered, %.',
    )
    ml_failures = serializers.IntegerField(
        help_text='Записи с ml_service_success=false (может пересекаться с timeouts).',
    )
    timeouts = serializers.IntegerField(
        help_text='Записи с пустым user_answer.',
    )
    ml_successful_validations = serializers.IntegerField(
        help_text='Записи с ml_service_success=true.',
    )
    avg_session_duration_sec = serializers.FloatField(
        help_text=(
            'Без attempt_number: среднее (completed_at − started_at) по завершённым LessonSession. '
            'С attempt_number: разница max−min answered_at по записям этой попытки.'
        ),
    )
    scope = serializers.ChoiceField(
        choices=['all', 'lesson', 'attempt'],
        required=False,
        help_text='all — без lesson_id; lesson — все попытки урока; attempt — одна попытка (attempt_number).',
    )
    lesson_title = serializers.CharField(
        allow_null=True,
        required=False,
        help_text='Название урока при переданном lesson_id (scope lesson или attempt).',
    )

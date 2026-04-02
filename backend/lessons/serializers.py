from rest_framework import serializers
from .models import Lesson, Question, InteractionRecord, LessonSession


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'order']
        read_only_fields = ['id']


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
    total_sessions = serializers.IntegerField()
    completed_sessions = serializers.IntegerField()
    total_questions_answered = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    success_rate = serializers.FloatField()
    ml_failures = serializers.IntegerField()
    timeouts = serializers.IntegerField()
    ml_successful_validations = serializers.IntegerField()
    avg_session_duration_sec = serializers.FloatField()

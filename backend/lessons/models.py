import random
import uuid
from django.db import models
from django.utils import timezone


class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    text = models.TextField(help_text="Text for user to read before questions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    correct_answer = models.CharField(max_length=255)
    distractor_1 = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Неверный вариант для демо (радиокнопки)',
    )
    distractor_2 = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Второй неверный вариант',
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def shuffled_choices(self):
        """Три варианта ответа; порядок стабилен для данного id вопроса."""
        d1 = (self.distractor_1 or '').strip() or 'Другое (неточно)'
        d2 = (self.distractor_2 or '').strip() or 'Нет однозначного ответа'
        pool = [self.correct_answer, d1, d2]
        out = []
        seen = set()
        for item in pool:
            if item not in seen:
                seen.add(item)
                out.append(item)
        i = 0
        while len(out) < 3:
            i += 1
            filler = f'Вариант {i}'
            if filler not in seen:
                seen.add(filler)
                out.append(filler)
        out = out[:3]
        rng = random.Random(int(self.id))
        rng.shuffle(out)
        return out

    def __str__(self):
        return f"Q{self.order}: {self.text[:50]}"


class InteractionRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=255, db_index=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='interactions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='interactions')
    user_answer = models.CharField(max_length=255, blank=True, default='')
    is_correct = models.BooleanField(null=True, help_text="Null if validation failed")
    ml_service_success = models.BooleanField(default=False)
    response_time = models.FloatField(null=True, help_text="Response time in seconds")
    answered_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    attempt_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['answered_at']
        indexes = [
            models.Index(fields=['session_id', 'lesson']),
            models.Index(fields=['session_id', 'lesson', 'attempt_number']),
            models.Index(fields=['answered_at']),
        ]

    def __str__(self):
        return f"{self.session_id} - Q{self.question.order} - {'✓' if self.is_correct else '✗'}"


class LessonSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=255, db_index=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='sessions')
    current_question_index = models.IntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)
    completion_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']
        constraints = [
            models.UniqueConstraint(
                fields=['session_id', 'lesson'],
                name='lessons_session_lesson_uniq',
            ),
        ]

    def __str__(self):
        return f"Session {self.session_id} - {self.lesson.title}"

    @property
    def success_rate(self):
        qs = self.lesson.interactions.filter(
            session_id=self.session_id,
            attempt_number=self.attempt_number,
        )
        total = qs.count()
        if total == 0:
            return 0
        correct = qs.filter(is_correct=True).count()
        return round((correct / total) * 100, 1)

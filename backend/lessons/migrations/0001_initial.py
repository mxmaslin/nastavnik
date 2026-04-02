# Generated manually for Nastavnik

import uuid
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('text', models.TextField(help_text='Text for user to read before questions')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('correct_answer', models.CharField(max_length=255)),
                ('order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='lessons.lesson')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='LessonSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_id', models.CharField(db_index=True, max_length=255)),
                ('current_question_index', models.IntegerField(default=0)),
                ('started_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='lessons.lesson')),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='lessonsession',
            constraint=models.UniqueConstraint(fields=('session_id', 'lesson'), name='lessons_session_lesson_uniq'),
        ),
        migrations.CreateModel(
            name='InteractionRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('session_id', models.CharField(db_index=True, max_length=255)),
                ('user_answer', models.CharField(blank=True, default='', max_length=255)),
                ('is_correct', models.BooleanField(help_text='Null if validation failed', null=True)),
                ('ml_service_success', models.BooleanField(default=False)),
                ('response_time', models.FloatField(help_text='Response time in seconds', null=True)),
                ('answered_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='lessons.lesson')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='lessons.question')),
            ],
            options={
                'ordering': ['answered_at'],
            },
        ),
        migrations.AddIndex(
            model_name='interactionrecord',
            index=models.Index(fields=['session_id', 'lesson'], name='lessons_inte_session_f1e4cb_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionrecord',
            index=models.Index(fields=['answered_at'], name='lessons_inte_answere_ae6002_idx'),
        ),
    ]

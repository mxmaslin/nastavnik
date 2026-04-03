# Generated manually

from django.db import migrations, models


def backfill_completion_count(apps, schema_editor):
    LessonSession = apps.get_model('lessons', 'LessonSession')
    for row in LessonSession.objects.filter(is_completed=True):
        row.completion_count = 1
        row.save(update_fields=['completion_count'])


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0002_question_distractors'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessonsession',
            name='attempt_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='lessonsession',
            name='completion_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='interactionrecord',
            name='attempt_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(backfill_completion_count, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name='interactionrecord',
            index=models.Index(
                fields=['session_id', 'lesson', 'attempt_number'],
                name='lessons_ir_sess_less_att',
            ),
        ),
    ]

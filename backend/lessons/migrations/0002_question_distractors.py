# Generated manually for multiple-choice demo fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='distractor_1',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Неверный вариант для демо (радиокнопки)',
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name='question',
            name='distractor_2',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Второй неверный вариант',
                max_length=255,
            ),
        ),
    ]

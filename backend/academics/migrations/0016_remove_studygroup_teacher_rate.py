from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0015_lesson_teacher'),
        ('finance', '0006_recalculate_draft_financial_documents'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studygroup',
            name='teacher_rate',
        ),
    ]

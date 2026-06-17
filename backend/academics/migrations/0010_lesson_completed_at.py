from django.db import migrations, models


def backfill_completed_at(apps, schema_editor):
    Lesson = apps.get_model('academics', 'Lesson')
    Lesson.objects.filter(status='completed', completed_at__isnull=True).update(completed_at=models.F('starts_at'))


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0009_groupattendancerate'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_completed_at, migrations.RunPython.noop),
    ]

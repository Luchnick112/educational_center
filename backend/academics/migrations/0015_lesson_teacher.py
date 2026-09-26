from django.db import migrations, models
import django.db.models.deletion


def backfill_lesson_teachers(apps, schema_editor):
    Lesson = apps.get_model('academics', 'Lesson')
    StudyGroup = apps.get_model('academics', 'StudyGroup')

    group_teachers = dict(StudyGroup.objects.values_list('id', 'teacher_id'))
    for lesson in Lesson.objects.only('id', 'group_id').iterator():
        Lesson.objects.filter(pk=lesson.pk).update(teacher_id=group_teachers[lesson.group_id])


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0014_remove_studygroup_capacity'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='teacher',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='lessons',
                to='users.teacherprofile',
            ),
        ),
        migrations.RunPython(backfill_lesson_teachers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='lesson',
            name='teacher',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='lessons',
                to='users.teacherprofile',
            ),
        ),
    ]

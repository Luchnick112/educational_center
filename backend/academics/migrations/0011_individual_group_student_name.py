from django.db import migrations


def rename_individual_groups(apps, schema_editor):
    StudyGroup = apps.get_model('academics', 'StudyGroup')
    StudentEnrollment = apps.get_model('academics', 'StudentEnrollment')

    for group in StudyGroup.objects.filter(format='individual'):
        enrollment = (
            StudentEnrollment.objects.select_related('student__user')
            .filter(group=group, status='active')
            .order_by('id')
            .first()
        )
        if enrollment is None:
            enrollment = (
                StudentEnrollment.objects.select_related('student__user')
                .filter(group=group)
                .order_by('id')
                .first()
            )
        if enrollment is None:
            continue

        last_name = (enrollment.student.user.last_name or '').strip()
        if not last_name:
            continue

        StudyGroup.objects.filter(pk=group.pk).update(name=f'{last_name}_{group.pk}')


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0010_lesson_completed_at'),
    ]

    operations = [
        migrations.RunPython(rename_individual_groups, migrations.RunPython.noop),
    ]

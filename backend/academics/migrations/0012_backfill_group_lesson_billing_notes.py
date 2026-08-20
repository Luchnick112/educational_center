from django.db import migrations


BILLING_LESSON_COUNT = 10


def backfill_group_lesson_billing_notes(apps, schema_editor):
    Lesson = apps.get_model('academics', 'Lesson')
    StudyGroup = apps.get_model('academics', 'StudyGroup')

    group_ids = StudyGroup.objects.filter(format='group').values_list('id', flat=True)
    for group_id in group_ids.iterator():
        lessons = (
            Lesson.objects.filter(group_id=group_id, status='completed')
            .order_by('completed_at', 'id')
            .values_list('id', flat=True)
        )
        for index, lesson_id in enumerate(lessons.iterator(), start=1):
            lesson_number = ((index - 1) % BILLING_LESSON_COUNT) + 1
            billing_note = str(lesson_number)
            lesson = Lesson.objects.get(pk=lesson_id)
            if lesson.notes == billing_note or lesson.notes.startswith(f'{billing_note}. '):
                continue
            notes = f'{billing_note}. {lesson.notes}' if lesson.notes else billing_note
            Lesson.objects.filter(pk=lesson_id).update(notes=notes)


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0011_individual_group_student_name'),
    ]

    operations = [
        migrations.RunPython(backfill_group_lesson_billing_notes, migrations.RunPython.noop),
    ]

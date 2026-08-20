from django.db import migrations


BILLING_LESSON_COUNT = 10


def remove_individual_lesson_billing_notes(apps, schema_editor):
    Lesson = apps.get_model('academics', 'Lesson')
    StudyGroup = apps.get_model('academics', 'StudyGroup')

    group_ids = StudyGroup.objects.filter(format='individual').values_list('id', flat=True)
    for group_id in group_ids.iterator():
        lessons = (
            Lesson.objects.filter(group_id=group_id, status='completed')
            .order_by('completed_at', 'id')
            .values_list('id', 'notes')
        )
        for index, (lesson_id, notes) in enumerate(lessons.iterator(), start=1):
            lesson_number = ((index - 1) % BILLING_LESSON_COUNT) + 1
            billing_note = str(lesson_number)
            if notes == billing_note:
                cleaned_notes = ''
            elif notes.startswith(f'{billing_note}. '):
                cleaned_notes = notes[len(billing_note) + 2:]
            else:
                continue
            Lesson.objects.filter(pk=lesson_id).update(notes=cleaned_notes)


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0012_backfill_group_lesson_billing_notes'),
    ]

    operations = [
        migrations.RunPython(remove_individual_lesson_billing_notes, migrations.RunPython.noop),
    ]

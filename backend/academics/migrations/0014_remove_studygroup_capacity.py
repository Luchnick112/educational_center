from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0013_remove_individual_lesson_billing_notes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studygroup',
            name='capacity',
        ),
    ]

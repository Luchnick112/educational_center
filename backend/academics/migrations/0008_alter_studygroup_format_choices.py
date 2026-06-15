from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0007_lessonreschedulerequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studygroup',
            name='format',
            field=models.CharField(
                choices=[
                    ('individual', 'Individual'),
                    ('group', 'Group'),
                ],
                default='group',
                max_length=16,
            ),
        ),
    ]

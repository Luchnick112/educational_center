from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_remove_studentprofile_date_of_birth'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentprofile',
            name='grade',
        ),
    ]

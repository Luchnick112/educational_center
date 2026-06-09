from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_remove_studentprofile_grade'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='lesson_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]

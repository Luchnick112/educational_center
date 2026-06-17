from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('finance', '0004_lessonteacherpayout'),
    ]

    operations = [
        migrations.AddField(
            model_name='parentcharge',
            name='billing_period',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='parentcharge',
            name='lesson_count',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='parentcharge',
            name='period_start_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parentcharge',
            name='period_end_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='teacherpayout',
            name='billing_period',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='teacherpayout',
            name='lesson_count',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='teacherpayout',
            name='period_start_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='teacherpayout',
            name='period_end_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lessonteacherpayout',
            name='billing_period',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='lessonteacherpayout',
            name='lesson_count',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='lessonteacherpayout',
            name='period_start_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lessonteacherpayout',
            name='period_end_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

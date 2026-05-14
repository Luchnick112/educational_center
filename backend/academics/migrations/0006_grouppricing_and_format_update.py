from django.db import migrations, models
from django.utils import timezone


def seed_group_pricing(apps, schema_editor):
    StudyGroup = apps.get_model('academics', 'StudyGroup')
    GroupPricing = apps.get_model('academics', 'GroupPricing')
    now = timezone.now()
    for group in StudyGroup.objects.all():
        GroupPricing.objects.get_or_create(
            group_id=group.id,
            effective_from=now,
            defaults={
                'student_price': group.student_price,
                'teacher_rate': group.teacher_rate,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0005_remove_lesson_title_ends_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studygroup',
            name='format',
            field=models.CharField(default='group', max_length=16),
        ),
        migrations.CreateModel(
            name='GroupPricing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('teacher_rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('effective_from', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='pricing_rules', to='academics.studygroup')),
            ],
            options={
                'ordering': ('-effective_from', '-id'),
            },
        ),
        migrations.RunPython(seed_group_pricing, migrations.RunPython.noop),
    ]

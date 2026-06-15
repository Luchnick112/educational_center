from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0008_alter_studygroup_format_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupAttendanceRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('present_count', models.PositiveIntegerField()),
                ('teacher_rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('effective_from', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_rates', to='academics.studygroup')),
            ],
            options={
                'ordering': ('group_id', 'present_count', '-effective_from', '-id'),
            },
        ),
    ]

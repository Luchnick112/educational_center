from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('academics', '0006_grouppricing_and_format_update'),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonRescheduleRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requested_starts_at', models.DateTimeField(blank=True, null=True)),
                ('reason', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('pending_parent', 'Pending parent confirmation'), ('parent_confirmed', 'Parent confirmed'), ('applied', 'Applied'), ('rejected', 'Rejected')], default='pending_parent', max_length=24)),
                ('parent_confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('applied_at', models.DateTimeField(blank=True, null=True)),
                ('new_starts_at', models.DateTimeField(blank=True, null=True)),
                ('teacher_comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('applied_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='applied_lesson_reschedules', to=settings.AUTH_USER_MODEL)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reschedule_requests', to='academics.lesson')),
                ('parent_confirmed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='parent_confirmed_lesson_reschedules', to=settings.AUTH_USER_MODEL)),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lesson_reschedule_requests', to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lesson_reschedule_requests', to='users.studentprofile')),
            ],
        ),
        migrations.AddConstraint(
            model_name='lessonreschedulerequest',
            constraint=models.UniqueConstraint(condition=models.Q(('status__in', ('pending_parent', 'parent_confirmed'))), fields=('lesson', 'student'), name='uniq_active_lesson_reschedule_request'),
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0009_groupattendancerate'),
        ('finance', '0003_studentpayment_teacherpayment'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonTeacherPayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('approved', 'Approved'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='draft', max_length=16)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_payout', to='academics.lesson')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lesson_payouts', to='users.teacherprofile')),
            ],
        ),
    ]

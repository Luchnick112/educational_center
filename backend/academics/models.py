from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from users.models import StudentProfile, TeacherProfile, User


class LessonFormat(models.TextChoices):
    GROUP = 'group', 'Group'
    INDIVIDUAL = 'individual', 'Individual'


class EnrollmentStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    PAUSED = 'paused', 'Paused'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class LessonStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class AttendanceStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    EXCUSED = 'excused', 'Excused'


class ConfirmationRequester(models.TextChoices):
    STUDENT = 'student', 'Student'
    PARENT = 'parent', 'Parent'
    TEACHER = 'teacher', 'Teacher'


class ConfirmationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    REJECTED = 'rejected', 'Rejected'


class Subject(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class StudyGroup(models.Model):
    # Auto-generated from subject_ + teacher.id_ + group.id (see save()).
    name = models.CharField(max_length=128, blank=True, default='')
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='groups')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name='groups')
    format = models.CharField(max_length=16, choices=LessonFormat.choices)
    capacity = models.PositiveIntegerField(default=1)
    student_price = models.DecimalField(max_digits=10, decimal_places=2)
    teacher_rate = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def _build_auto_name(self) -> str:
        if not (self.subject_id and self.teacher_id and self.pk):
            return self.name
        return f'{self.subject}+{self.teacher_id}+{self.pk}'

    def save(self, *args, **kwargs):
        # We need `pk` for the name, so on create we save once, then set name.
        if self.pk is None:
            super().save(*args, **kwargs)
            auto_name = self._build_auto_name()
            if self.name != auto_name:
                StudyGroup.objects.filter(pk=self.pk).update(name=auto_name)
                self.name = auto_name
            return

        auto_name = self._build_auto_name()
        if self.name != auto_name:
            self.name = auto_name
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = list(set(kwargs['update_fields']) | {'name'})
        super().save(*args, **kwargs)

    def clean(self) -> None:
        if self.format == LessonFormat.INDIVIDUAL and self.capacity != 1:
            raise ValidationError('Individual groups must have capacity 1.')

    def __str__(self) -> str:
        return f'{self.name} [{self.get_format_display()}]'


class StudentEnrollment(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    status = models.CharField(max_length=16, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    student_price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    teacher_rate_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('group', 'student')

    @property
    def student_price(self) -> Decimal:
        return self.student_price_override or self.group.student_price

    @property
    def teacher_rate(self) -> Decimal:
        return self.teacher_rate_override or self.group.teacher_rate

    def __str__(self) -> str:
        return f'{self.student} / {self.group}'


class Lesson(models.Model):
    DEFAULT_DURATION = timedelta(hours=1)

    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='lessons')
    starts_at = models.DateTimeField()
    status = models.CharField(max_length=16, choices=LessonStatus.choices, default=LessonStatus.SCHEDULED)
    notes = models.TextField(blank=True)

    @property
    def end_at(self):
        # Lesson duration is fixed by product requirement: 1 lesson == 1 hour.
        return self.starts_at + self.DEFAULT_DURATION

    def __str__(self) -> str:
        return f'{self.group} @ {self.starts_at}'


class LessonParticipant(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='participants')
    enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.PROTECT,
        related_name='lesson_participations',
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='lesson_participations')
    attendance_status = models.CharField(
        max_length=16,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PENDING,
    )
    billed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payroll_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = ('lesson', 'student')

    def save(self, *args, **kwargs):
        if not self.billed_amount:
            self.billed_amount = self.enrollment.student_price
        if not self.payroll_amount:
            self.payroll_amount = self.enrollment.teacher_rate
        self.student = self.enrollment.student
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'{self.lesson} / {self.student}'


class LessonConfirmation(models.Model):
    participant = models.ForeignKey(LessonParticipant, on_delete=models.CASCADE, related_name='confirmations')
    requested_from = models.CharField(max_length=16, choices=ConfirmationRequester.choices)
    confirmer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_confirmations',
    )
    status = models.CharField(max_length=16, choices=ConfirmationStatus.choices, default=ConfirmationStatus.PENDING)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('participant', 'requested_from')

    def __str__(self) -> str:
        return f'{self.participant} / {self.requested_from}'

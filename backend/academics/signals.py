from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

from finance.models import LessonTeacherPayout, ParentCharge, TeacherPayout
from users.models import StudentParentRelation

from .models import (
    AttendanceStatus,
    GroupAttendanceRate,
    Lesson,
    LessonParticipant,
    LessonStatus,
    StudyGroupFormat,
    StudentEnrollment,
)


def group_lesson_teacher_amount(lesson: Lesson) -> Decimal:
    present_count = lesson.participants.filter(attendance_status=AttendanceStatus.PRESENT).count()
    if present_count <= 0:
        return Decimal('0.00')

    rate = (
        GroupAttendanceRate.objects.filter(
            group=lesson.group,
            present_count__lte=present_count,
            effective_from__lte=lesson.starts_at,
        )
        .order_by('-present_count', '-effective_from', '-id')
        .first()
    )
    if rate:
        return rate.teacher_rate

    _, teacher_rate = lesson.group.get_effective_pricing(lesson.starts_at)
    return teacher_rate


@receiver(post_save, sender=Lesson)
def create_lesson_participants(sender, instance: Lesson, created: bool, **kwargs):
    if kwargs.get('raw') or not created:
        return

    enrollments = StudentEnrollment.objects.filter(
        group=instance.group,
        status='active',
    ).select_related('student')

    for enrollment in enrollments:
        LessonParticipant.objects.get_or_create(
            lesson=instance,
            student=enrollment.student,
            defaults={'enrollment': enrollment},
        )


@receiver(post_save, sender=Lesson)
def create_financial_documents(sender, instance: Lesson, created: bool, **kwargs):
    if kwargs.get('raw') or created or instance.status != LessonStatus.COMPLETED:
        return

    participants = instance.participants.select_related(
        'student',
        'enrollment',
        'enrollment__group',
        'enrollment__group__teacher',
    )

    for participant in participants:
        relation = (
            StudentParentRelation.objects.filter(
                student=participant.student,
                is_financial_contact=True,
            )
            .select_related('parent')
            .first()
        )
        if relation:
            ParentCharge.objects.get_or_create(
                participant=participant,
                defaults={
                    'parent': relation.parent,
                    'student': participant.student,
                    'amount': participant.billed_amount,
                },
            )

    if instance.group.format == StudyGroupFormat.GROUP:
        LessonTeacherPayout.objects.get_or_create(
            lesson=instance,
            defaults={
                'teacher': instance.group.teacher,
                'amount': group_lesson_teacher_amount(instance),
            },
        )
        return

    for participant in participants:
        TeacherPayout.objects.get_or_create(
            participant=participant,
            defaults={
                'teacher': participant.enrollment.group.teacher,
                'amount': participant.payroll_amount if participant.attendance_status == AttendanceStatus.PRESENT else 0,
            },
        )

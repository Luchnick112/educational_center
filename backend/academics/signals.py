from django.db.models.signals import post_save
from django.dispatch import receiver

from finance.models import ParentCharge, TeacherPayout
from users.models import StudentParentRelation

from .models import (
    AttendanceStatus,
    Lesson,
    LessonParticipant,
    LessonStatus,
    StudentEnrollment,
)


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

        TeacherPayout.objects.get_or_create(
            participant=participant,
            defaults={
                'teacher': participant.enrollment.group.teacher,
                'amount': participant.payroll_amount if participant.attendance_status == AttendanceStatus.PRESENT else 0,
            },
        )

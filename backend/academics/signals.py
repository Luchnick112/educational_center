from decimal import Decimal

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from finance.models import LessonTeacherPayout, ParentCharge, PayoutStatus, TeacherPayout
from users.models import StudentParentRelation

from .constants import BILLING_LESSON_COUNT
from .models import (
    AttendanceStatus,
    GroupAttendanceRate,
    Lesson,
    LessonParticipant,
    LessonStatus,
    StudyGroupFormat,
)
from .services import create_lesson_participants_for_enrollments, group_lesson_teacher_amount


def completed_lessons_count(group) -> int:
    return group.lessons.filter(status=LessonStatus.COMPLETED).count()


def lessons_until_next_billing(group) -> int:
    completed_count = completed_lessons_count(group)
    remainder = completed_count % BILLING_LESSON_COUNT
    if remainder == 0:
        return BILLING_LESSON_COUNT
    return BILLING_LESSON_COUNT - remainder


def _completed_lesson_batch(lesson: Lesson) -> tuple[int, list[Lesson]]:
    completed_lessons = list(
        Lesson.objects.filter(
            group=lesson.group,
            status=LessonStatus.COMPLETED,
        ).order_by('completed_at', 'id')
    )
    if len(completed_lessons) == 0 or len(completed_lessons) % BILLING_LESSON_COUNT != 0:
        return 0, []

    batch_number = len(completed_lessons) // BILLING_LESSON_COUNT
    return batch_number, completed_lessons[-BILLING_LESSON_COUNT:]


def _batch_period(batch: list[Lesson]):
    starts = [lesson.starts_at for lesson in batch]
    return min(starts), max(starts)


def _create_parent_charges_for_batch(*, batch_number: int, batch: list[Lesson]) -> None:
    period_start_at, period_end_at = _batch_period(batch)
    participants = (
        LessonParticipant.objects.filter(lesson__in=batch)
        .select_related('student')
        .order_by('lesson__starts_at', 'lesson_id', 'id')
    )
    participants_by_student = {}
    for participant in participants:
        participants_by_student.setdefault(participant.student_id, []).append(participant)

    for student_participants in participants_by_student.values():
        billing_participant = student_participants[-1]
        relation = (
            StudentParentRelation.objects.filter(
                student=billing_participant.student,
                is_financial_contact=True,
            )
            .select_related('parent')
            .first()
        )
        if relation is None:
            continue

        ParentCharge.objects.get_or_create(
            participant=billing_participant,
            defaults={
                'parent': relation.parent,
                'student': billing_participant.student,
                'amount': sum((item.billed_amount for item in student_participants), Decimal('0.00')),
                'billing_period': batch_number,
                'lesson_count': len(student_participants),
                'period_start_at': period_start_at,
                'period_end_at': period_end_at,
            },
        )


def _create_group_teacher_payout_for_batch(*, batch_number: int, batch: list[Lesson]) -> None:
    period_start_at, period_end_at = _batch_period(batch)
    billing_lesson = batch[-1]
    amount = sum((group_lesson_teacher_amount(lesson) for lesson in batch), Decimal('0.00'))
    payout, created = LessonTeacherPayout.objects.get_or_create(
        lesson=billing_lesson,
        defaults={
            'teacher': billing_lesson.group.teacher,
            'amount': amount,
            'billing_period': batch_number,
            'lesson_count': len(batch),
            'period_start_at': period_start_at,
            'period_end_at': period_end_at,
        },
    )
    if not created and payout.status == PayoutStatus.DRAFT and payout.amount != amount:
        payout.amount = amount
        payout.save(update_fields=['amount'])


def _lesson_teacher_payout_lessons(payout: LessonTeacherPayout):
    if payout.lesson_count == 1:
        return [payout.lesson]
    if payout.period_start_at is None or payout.period_end_at is None:
        return [payout.lesson]
    return list(
        Lesson.objects.filter(
            group=payout.lesson.group,
            status=LessonStatus.COMPLETED,
            starts_at__gte=payout.period_start_at,
            starts_at__lte=payout.period_end_at,
        ).order_by('starts_at', 'id')
    )


def _recalculate_draft_lesson_teacher_payout(payout: LessonTeacherPayout) -> None:
    amount = sum(
        (group_lesson_teacher_amount(lesson) for lesson in _lesson_teacher_payout_lessons(payout)),
        Decimal('0.00'),
    )
    if payout.amount != amount:
        payout.amount = amount
        payout.save(update_fields=['amount'])


def _recalculate_draft_lesson_teacher_payouts_for_group(group) -> None:
    payouts = LessonTeacherPayout.objects.filter(
        lesson__group=group,
        status=PayoutStatus.DRAFT,
    ).select_related('lesson', 'lesson__group')
    for payout in payouts:
        _recalculate_draft_lesson_teacher_payout(payout)


def _create_individual_financial_documents(lesson: Lesson) -> None:
    participants = lesson.participants.select_related(
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
                    'period_start_at': lesson.starts_at,
                    'period_end_at': lesson.starts_at,
                },
            )

        TeacherPayout.objects.get_or_create(
            participant=participant,
            defaults={
                'teacher': participant.enrollment.group.teacher,
                'amount': participant.payroll_amount if participant.attendance_status == AttendanceStatus.PRESENT else 0,
                'period_start_at': lesson.starts_at,
                'period_end_at': lesson.starts_at,
            },
        )


@receiver(post_save, sender=Lesson)
def create_lesson_participants(sender, instance: Lesson, created: bool, **kwargs):
    if kwargs.get('raw') or not created:
        return

    create_lesson_participants_for_enrollments(instance)


@receiver(post_save, sender=Lesson)
def create_financial_documents(sender, instance: Lesson, created: bool, **kwargs):
    if kwargs.get('raw') or created or instance.status != LessonStatus.COMPLETED:
        return

    if instance.completed_at is None:
        instance.completed_at = timezone.now()
        Lesson.objects.filter(pk=instance.pk, completed_at__isnull=True).update(completed_at=instance.completed_at)

    if instance.group.format != StudyGroupFormat.GROUP:
        _create_individual_financial_documents(instance)
        return

    batch_number, batch = _completed_lesson_batch(instance)
    if not batch:
        return

    _create_parent_charges_for_batch(batch_number=batch_number, batch=batch)
    _create_group_teacher_payout_for_batch(batch_number=batch_number, batch=batch)


@receiver(post_save, sender=GroupAttendanceRate)
def recalculate_group_draft_payouts_after_attendance_rate_save(sender, instance: GroupAttendanceRate, **kwargs):
    if kwargs.get('raw'):
        return
    _recalculate_draft_lesson_teacher_payouts_for_group(instance.group)


@receiver(post_delete, sender=GroupAttendanceRate)
def recalculate_group_draft_payouts_after_attendance_rate_delete(sender, instance: GroupAttendanceRate, **kwargs):
    _recalculate_draft_lesson_teacher_payouts_for_group(instance.group)

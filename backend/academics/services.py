from django.utils import timezone
from rest_framework import exceptions

from users.models import UserRole

from .models import (
    AttendanceStatus,
    ConfirmationRequester,
    ConfirmationStatus,
    Lesson,
    LessonConfirmation,
    LessonRescheduleRequest,
    LessonRescheduleStatus,
    LessonStatus,
)


def ensure_lesson_teacher_or_admin(user, lesson: Lesson, action_label: str) -> None:
    if user.is_staff or user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile') and lesson.group.teacher == user.teacher_profile:
        return
    raise exceptions.PermissionDenied(f'You cannot {action_label} for this lesson.')


def ensure_admin(user, action_label: str) -> None:
    if user.is_staff or user.role == UserRole.ADMIN:
        return
    raise exceptions.PermissionDenied(f'Only admins can {action_label}.')


def ensure_individual_scheduled_lesson(lesson: Lesson) -> None:
    if lesson.status != LessonStatus.SCHEDULED:
        raise exceptions.ValidationError({'lesson': 'Only scheduled lessons can be rescheduled.'})
    if lesson.group.enrollments.filter(status='active').count() != 1 or lesson.participants.count() != 1:
        raise exceptions.ValidationError({'lesson': 'Reschedule requests are available only for individual lessons.'})


def mark_lesson_attendance(*, user, lesson: Lesson, participant_id: int, attendance_status: str) -> dict:
    ensure_lesson_teacher_or_admin(user, lesson, 'mark attendance')
    if lesson.status != LessonStatus.SCHEDULED:
        raise exceptions.ValidationError({'detail': 'Attendance can only be updated for scheduled lessons.'})

    participant = lesson.participants.filter(pk=participant_id).first()
    if participant is None:
        raise exceptions.NotFound('Participant does not belong to this lesson.')

    participant.attendance_status = attendance_status
    if attendance_status == AttendanceStatus.PRESENT:
        _, base_teacher_rate = participant.lesson.group.get_effective_pricing(participant.lesson.starts_at)
        participant.payroll_amount = participant.enrollment.teacher_rate_override or base_teacher_rate
    else:
        participant.payroll_amount = 0
    participant.save(update_fields=['attendance_status', 'payroll_amount'])
    return {
        'participant_id': participant.id,
        'attendance_status': participant.attendance_status,
        'payroll_amount': participant.payroll_amount,
    }


def complete_lesson(*, user, lesson: Lesson, notes: str = '') -> Lesson:
    ensure_lesson_teacher_or_admin(user, lesson, 'complete this lesson')
    if lesson.status != LessonStatus.SCHEDULED:
        raise exceptions.ValidationError({'detail': 'Only scheduled lessons can be completed.'})
    if not lesson.participants.exists():
        raise exceptions.ValidationError({'detail': 'Lesson has no participants.'})
    if lesson.participants.filter(attendance_status=AttendanceStatus.PENDING).exists():
        raise exceptions.ValidationError(
            {'detail': 'All participants must have attendance marked before completion.'}
        )

    if notes:
        lesson.notes = notes
    lesson.status = LessonStatus.COMPLETED
    lesson.save()
    confirm_lesson_confirmations(user=user, lesson=lesson)
    return lesson


def cancel_lesson(*, user, lesson: Lesson, reason: str) -> Lesson:
    ensure_admin(user, 'cancel lessons')
    if lesson.status != LessonStatus.SCHEDULED:
        raise exceptions.ValidationError({'detail': 'Only scheduled lessons can be cancelled.'})

    lesson.status = LessonStatus.CANCELLED
    lesson.notes = reason
    lesson.save(update_fields=['status', 'notes'])
    reject_lesson_confirmations(user=user, lesson=lesson)
    return lesson


def create_lesson_reschedule_request(*, user, lesson: Lesson, requested_starts_at=None, reason: str = '') -> LessonRescheduleRequest:
    if user.role != UserRole.STUDENT or not hasattr(user, 'student_profile'):
        raise exceptions.PermissionDenied('Only students can request lesson rescheduling.')

    ensure_individual_scheduled_lesson(lesson)

    participant = lesson.participants.filter(student=user.student_profile).first()
    if participant is None:
        raise exceptions.PermissionDenied('You can request rescheduling only for your own lesson.')

    if requested_starts_at is not None and requested_starts_at <= timezone.now():
        raise exceptions.ValidationError({'requested_starts_at': 'Requested time must be in the future.'})

    has_active_request = LessonRescheduleRequest.objects.filter(
        lesson=lesson,
        student=user.student_profile,
        status__in=(LessonRescheduleStatus.PENDING_PARENT, LessonRescheduleStatus.PARENT_CONFIRMED),
    ).exists()
    if has_active_request:
        raise exceptions.ValidationError({'lesson': 'This lesson already has an active reschedule request.'})

    return LessonRescheduleRequest.objects.create(
        lesson=lesson,
        student=user.student_profile,
        requested_by=user,
        requested_starts_at=requested_starts_at,
        reason=reason,
    )


def confirm_lesson_reschedule_by_parent(*, user, reschedule_request: LessonRescheduleRequest) -> LessonRescheduleRequest:
    if user.role != UserRole.PARENT or not hasattr(user, 'parent_profile'):
        raise exceptions.PermissionDenied('Only parents can confirm lesson reschedule requests.')

    is_related_parent = reschedule_request.student.parent_links.filter(parent=user.parent_profile).exists()
    if not is_related_parent:
        raise exceptions.PermissionDenied('This reschedule request is not available for this parent.')

    ensure_individual_scheduled_lesson(reschedule_request.lesson)

    if reschedule_request.status == LessonRescheduleStatus.PARENT_CONFIRMED:
        return reschedule_request
    if reschedule_request.status != LessonRescheduleStatus.PENDING_PARENT:
        raise exceptions.ValidationError({'status': 'Only pending parent requests can be confirmed.'})

    reschedule_request.status = LessonRescheduleStatus.PARENT_CONFIRMED
    reschedule_request.parent_confirmed_by = user
    reschedule_request.parent_confirmed_at = timezone.now()
    reschedule_request.save(update_fields=('status', 'parent_confirmed_by', 'parent_confirmed_at', 'updated_at'))
    return reschedule_request


def apply_lesson_reschedule(*, user, reschedule_request: LessonRescheduleRequest, starts_at, teacher_comment: str = '') -> LessonRescheduleRequest:
    if not (
        user.is_staff
        or user.role == UserRole.ADMIN
        or (
            user.role == UserRole.TEACHER
            and hasattr(user, 'teacher_profile')
            and reschedule_request.lesson.group.teacher_id == user.teacher_profile.id
        )
    ):
        raise exceptions.PermissionDenied('Only the lesson teacher can apply reschedule requests.')

    ensure_individual_scheduled_lesson(reschedule_request.lesson)

    if reschedule_request.status != LessonRescheduleStatus.PARENT_CONFIRMED:
        raise exceptions.ValidationError({'status': 'Parent confirmation is required before rescheduling.'})
    if starts_at <= timezone.now():
        raise exceptions.ValidationError({'starts_at': 'New lesson time must be in the future.'})

    lesson = reschedule_request.lesson
    lesson.starts_at = starts_at
    lesson.save(update_fields=('starts_at',))

    reschedule_request.status = LessonRescheduleStatus.APPLIED
    reschedule_request.applied_by = user
    reschedule_request.applied_at = timezone.now()
    reschedule_request.new_starts_at = starts_at
    reschedule_request.teacher_comment = teacher_comment
    reschedule_request.save(
        update_fields=(
            'status',
            'applied_by',
            'applied_at',
            'new_starts_at',
            'teacher_comment',
            'updated_at',
        )
    )
    return reschedule_request


def confirm_lesson(*, user, confirmation: LessonConfirmation, comment: str = '') -> LessonConfirmation:
    expected_requester = None

    if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
        if confirmation.participant.student_id != user.student_profile.id:
            raise exceptions.PermissionDenied('Confirmation is not available for this student.')
        expected_requester = ConfirmationRequester.STUDENT
    elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
        is_related_parent = confirmation.participant.student.parent_links.filter(parent=user.parent_profile).exists()
        if not is_related_parent:
            raise exceptions.PermissionDenied('Confirmation is not available for this parent.')
        expected_requester = ConfirmationRequester.PARENT
    elif user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
        if confirmation.participant.lesson.group.teacher_id != user.teacher_profile.id:
            raise exceptions.PermissionDenied('Confirmation is not available for this teacher.')
        expected_requester = ConfirmationRequester.TEACHER
    elif user.is_staff or user.role == UserRole.ADMIN:
        expected_requester = confirmation.requested_from
    else:
        raise exceptions.PermissionDenied('You cannot confirm this lesson.')

    if confirmation.requested_from != expected_requester:
        raise exceptions.ValidationError({'detail': 'This confirmation is assigned to another role.'})
    if confirmation.status == ConfirmationStatus.CONFIRMED:
        return confirmation

    confirmation.status = ConfirmationStatus.CONFIRMED
    confirmation.confirmer = user
    confirmation.confirmed_at = timezone.now()
    confirmation.comment = comment or confirmation.comment
    confirmation.save(update_fields=['status', 'confirmer', 'confirmed_at', 'comment'])
    return confirmation


def confirm_lesson_confirmations(*, user, lesson: Lesson) -> int:
    return LessonConfirmation.objects.filter(
        participant__lesson=lesson,
        status=ConfirmationStatus.PENDING,
    ).update(
        status=ConfirmationStatus.CONFIRMED,
        confirmer=user,
        confirmed_at=timezone.now(),
    )


def reject_lesson_confirmations(*, user, lesson: Lesson) -> int:
    return LessonConfirmation.objects.filter(
        participant__lesson=lesson,
        status=ConfirmationStatus.PENDING,
    ).update(
        status=ConfirmationStatus.REJECTED,
        confirmer=user,
        confirmed_at=timezone.now(),
    )

from django.utils import timezone
from rest_framework import exceptions

from users.models import UserRole

from .models import (
    AttendanceStatus,
    ConfirmationRequester,
    ConfirmationStatus,
    Lesson,
    LessonConfirmation,
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


def mark_lesson_attendance(*, user, lesson: Lesson, participant_id: int, attendance_status: str) -> dict:
    ensure_lesson_teacher_or_admin(user, lesson, 'mark attendance')
    if lesson.status != LessonStatus.SCHEDULED:
        raise exceptions.ValidationError({'detail': 'Attendance can only be updated for scheduled lessons.'})

    participant = lesson.participants.filter(pk=participant_id).first()
    if participant is None:
        raise exceptions.NotFound('Participant does not belong to this lesson.')

    participant.attendance_status = attendance_status
    participant.save(update_fields=['attendance_status'])
    return {'participant_id': participant.id, 'attendance_status': participant.attendance_status}


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
    return lesson


def cancel_lesson(*, user, lesson: Lesson, reason: str) -> Lesson:
    ensure_admin(user, 'cancel lessons')
    if lesson.status != LessonStatus.SCHEDULED:
        raise exceptions.ValidationError({'detail': 'Only scheduled lessons can be cancelled.'})

    lesson.status = LessonStatus.CANCELLED
    lesson.notes = reason
    lesson.save(update_fields=['status', 'notes'])
    return lesson


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

from rest_framework import exceptions

from finance.models import ParentCharge, TeacherPayout
from users.models import ParentProfile, TeacherProfile, User, UserRole

from academics.models import AttendanceStatus, ConfirmationRequester, ConfirmationStatus, LessonStatus
from academics.services import cancel_lesson, complete_lesson, confirm_lesson, mark_lesson_attendance
from academics.tests.base import AcademicBaseTestCase


class AcademicServicesTestCase(AcademicBaseTestCase):
    def test_mark_lesson_attendance_updates_participant(self):
        participant = self.lesson.participants.get()

        result = mark_lesson_attendance(
            user=self.teacher_user,
            lesson=self.lesson,
            participant_id=participant.id,
            attendance_status=AttendanceStatus.PRESENT,
        )

        participant.refresh_from_db()

        self.assertEqual(result['participant_id'], participant.id)
        self.assertEqual(participant.attendance_status, AttendanceStatus.PRESENT)

    def test_mark_lesson_attendance_denies_unrelated_parent(self):
        other_parent_user = User.objects.create_user(
            username='service_parent',
            email='service_parent@example.com',
            password='pass12345',
            role=UserRole.PARENT,
        )
        ParentProfile.objects.create(user=other_parent_user)
        participant = self.lesson.participants.get()

        with self.assertRaises(exceptions.PermissionDenied):
            mark_lesson_attendance(
                user=other_parent_user,
                lesson=self.lesson,
                participant_id=participant.id,
                attendance_status=AttendanceStatus.PRESENT,
            )

    def test_complete_lesson_sets_status_and_triggers_financial_documents(self):
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])

        lesson = complete_lesson(
            user=self.teacher_user,
            lesson=self.lesson,
            notes='Service completed lesson',
        )

        self.assertEqual(lesson.status, LessonStatus.COMPLETED)
        self.assertEqual(lesson.notes, 'Service completed lesson')
        self.assertTrue(ParentCharge.objects.filter(participant=participant).exists())
        self.assertTrue(TeacherPayout.objects.filter(participant=participant).exists())

    def test_complete_lesson_rejects_pending_attendance(self):
        with self.assertRaises(exceptions.ValidationError):
            complete_lesson(user=self.teacher_user, lesson=self.lesson, notes='')

    def test_cancel_lesson_is_admin_only(self):
        with self.assertRaises(exceptions.PermissionDenied):
            cancel_lesson(user=self.teacher_user, lesson=self.lesson, reason='No access')

    def test_confirm_lesson_marks_expected_confirmation(self):
        participant = self.lesson.participants.get()
        confirmation = participant.confirmations.get(requested_from=ConfirmationRequester.STUDENT)

        result = confirm_lesson(
            user=self.student_user,
            confirmation=confirmation,
            comment='Confirmed by service',
        )

        confirmation.refresh_from_db()

        self.assertEqual(result.status, ConfirmationStatus.CONFIRMED)
        self.assertEqual(confirmation.confirmer, self.student_user)
        self.assertEqual(confirmation.comment, 'Confirmed by service')

    def test_confirm_lesson_rejects_wrong_role(self):
        participant = self.lesson.participants.get()
        confirmation = participant.confirmations.get(requested_from=ConfirmationRequester.PARENT)

        with self.assertRaises(exceptions.ValidationError):
            confirm_lesson(
                user=self.student_user,
                confirmation=confirmation,
                comment='Wrong role',
            )

from finance.models import TeacherPayout
from users.models import ParentProfile, TeacherProfile, User, UserRole

from academics.models import AttendanceStatus
from academics.tests.base import AcademicBaseTestCase


class AcademicPermissionsTestCase(AcademicBaseTestCase):
    def test_parent_cannot_access_unrelated_student_lesson_by_direct_url(self):
        other_parent_user = User.objects.create_user(
            username='other_parent',
            email='other_parent@example.com',
            password='pass12345',
            role=UserRole.PARENT,
        )
        ParentProfile.objects.create(user=other_parent_user)
        self.client.force_authenticate(other_parent_user)

        response = self.client.get(f'/api/academics/lessons/{self.lesson.id}/')

        self.assertEqual(response.status_code, 404)

    def test_teacher_cannot_access_other_teacher_payout_by_direct_url(self):
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        self.client.force_authenticate(self.teacher_user)
        self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/complete/',
            {'notes': 'Prepare payout'},
            format='json',
        )
        payout = TeacherPayout.objects.get(participant=participant)

        other_teacher_user = User.objects.create_user(
            username='other_teacher',
            email='other_teacher@example.com',
            password='pass12345',
            role=UserRole.TEACHER,
        )
        TeacherProfile.objects.create(user=other_teacher_user, hourly_rate=200)
        self.client.force_authenticate(other_teacher_user)

        response = self.client.get(f'/api/finance/teacher-payouts/{payout.id}/')

        self.assertEqual(response.status_code, 404)

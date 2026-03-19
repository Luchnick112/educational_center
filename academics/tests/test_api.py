from finance.models import ChargeStatus, ParentCharge, PayoutStatus, TeacherPayout
from users.models import ParentProfile, TeacherProfile, User, UserRole

from academics.models import AttendanceStatus, ConfirmationRequester, LessonStatus
from academics.tests.base import AcademicBaseTestCase


class RoleAwareApiTestCase(AcademicBaseTestCase):
    def test_register_page_is_available_in_browser(self):
        response = self.client.get('/api/users/register/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create a new account')

    def test_token_page_is_available_in_browser(self):
        response = self.client.get('/api/users/token/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Get access tokens')

    def test_token_refresh_page_is_available_in_browser(self):
        response = self.client.get('/api/users/token/refresh/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Refresh access token')

    def test_student_me_and_my_lessons_endpoints(self):
        self.client.force_authenticate(self.student_user)

        me_response = self.client.get('/api/me/')
        lessons_response = self.client.get('/api/my-lessons/')
        payments_response = self.client.get('/api/my-payments/')

        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data['role'], UserRole.STUDENT)
        self.assertEqual(lessons_response.status_code, 200)
        self.assertEqual(len(lessons_response.data), 1)
        self.assertEqual(payments_response.status_code, 200)

    def test_parent_sees_only_linked_children(self):
        self.client.force_authenticate(self.parent_user)

        children_response = self.client.get('/api/my-children/')
        confirmations_response = self.client.get('/api/my-confirmations/')

        self.assertEqual(children_response.status_code, 200)
        self.assertEqual(len(children_response.data), 1)
        self.assertEqual(children_response.data[0]['id'], self.student.id)
        self.assertEqual(confirmations_response.status_code, 200)

    def test_register_creates_user_and_role_profile(self):
        response = self.client.post(
            '/api/users/register/',
            {
                'password': 'pass12345',
                'first_name': 'New',
                'last_name': 'Teacher',
                'email': 'teacher@example.com',
                'role': UserRole.TEACHER,
                'phone': '+380001112233',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        created_user = User.objects.get(email='teacher@example.com')
        self.assertTrue(hasattr(created_user, 'teacher_profile'))
        self.assertEqual(response.data['email'], 'teacher@example.com')

    def test_token_obtain_uses_email_instead_of_username(self):
        response = self.client.post(
            '/api/users/token/',
            {
                'email': 'teacher_api@example.com',
                'password': 'pass12345',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_teacher_can_mark_attendance_and_complete_lesson(self):
        participant = self.lesson.participants.get()
        self.client.force_authenticate(self.teacher_user)

        attendance_response = self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/mark-attendance/',
            {
                'participant_id': participant.id,
                'attendance_status': AttendanceStatus.PRESENT,
            },
            format='json',
        )
        complete_response = self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/complete/',
            {'notes': 'Completed on time'},
            format='json',
        )

        self.lesson.refresh_from_db()
        participant.refresh_from_db()

        self.assertEqual(attendance_response.status_code, 200)
        self.assertEqual(participant.attendance_status, AttendanceStatus.PRESENT)
        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(self.lesson.status, LessonStatus.COMPLETED)
        self.assertTrue(ParentCharge.objects.filter(participant=participant).exists())
        self.assertTrue(TeacherPayout.objects.filter(participant=participant).exists())

    def test_student_can_confirm_own_confirmation_only(self):
        participant = self.lesson.participants.get()
        student_confirmation = participant.confirmations.get(requested_from=ConfirmationRequester.STUDENT)
        parent_confirmation = participant.confirmations.get(requested_from=ConfirmationRequester.PARENT)
        self.client.force_authenticate(self.student_user)

        ok_response = self.client.post(
            f'/api/academics/confirmations/{student_confirmation.id}/confirm/',
            {'comment': 'Done'},
            format='json',
        )
        forbidden_response = self.client.post(
            f'/api/academics/confirmations/{parent_confirmation.id}/confirm/',
            {'comment': 'Wrong role'},
            format='json',
        )

        student_confirmation.refresh_from_db()

        self.assertEqual(ok_response.status_code, 200)
        self.assertEqual(student_confirmation.status, 'confirmed')
        self.assertEqual(forbidden_response.status_code, 404)

    def test_admin_can_cancel_scheduled_lesson(self):
        admin_user = User.objects.create_user(
            username='admin_api',
            email='admin_api@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        response = self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/cancel/',
            {'reason': 'Teacher sick leave'},
            format='json',
        )

        self.lesson.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.lesson.status, LessonStatus.CANCELLED)
        self.assertEqual(self.lesson.notes, 'Teacher sick leave')

    def test_admin_can_run_finance_workflow_actions(self):
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        self.client.force_authenticate(self.teacher_user)
        self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/complete/',
            {'notes': 'Completed for finance workflow'},
            format='json',
        )

        charge = ParentCharge.objects.get(participant=participant)
        payout = TeacherPayout.objects.get(participant=participant)

        admin_user = User.objects.create_user(
            username='finance_admin',
            email='finance_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        issue_response = self.client.post(
            f'/api/finance/parent-charges/{charge.id}/issue/',
            {'due_date': '2026-03-31'},
            format='json',
        )
        charge_paid_response = self.client.post(
            f'/api/finance/parent-charges/{charge.id}/mark-paid/',
            {},
            format='json',
        )
        approve_response = self.client.post(
            f'/api/finance/teacher-payouts/{payout.id}/approve/',
            {},
            format='json',
        )
        payout_paid_response = self.client.post(
            f'/api/finance/teacher-payouts/{payout.id}/mark-paid/',
            {},
            format='json',
        )

        charge.refresh_from_db()
        payout.refresh_from_db()

        self.assertEqual(issue_response.status_code, 200)
        self.assertEqual(charge_paid_response.status_code, 200)
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(payout_paid_response.status_code, 200)
        self.assertEqual(charge.status, ChargeStatus.PAID)
        self.assertEqual(str(charge.due_date), '2026-03-31')
        self.assertIsNotNone(charge.paid_at)
        self.assertEqual(payout.status, PayoutStatus.PAID)
        self.assertIsNotNone(payout.approved_at)
        self.assertIsNotNone(payout.paid_at)

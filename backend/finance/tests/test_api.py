from datetime import timedelta

from django.utils import timezone

from academics.models import AttendanceStatus, Lesson
from academics.services import complete_lesson
from academics.tests.base import AcademicBaseTestCase
from finance.models import StudentPayment, TeacherPayment
from finance.services import mark_parent_charge_paid
from users.models import User, UserRole


class MyPaymentsApiTestCase(AcademicBaseTestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_user(
            username='payments_admin',
            email='payments_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )

    def complete_lesson_with_finance_docs(self, lesson):
        participant = lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        complete_lesson(user=self.teacher_user, lesson=lesson)
        return lesson.participants.get()

    def test_admin_payments_include_student_and_teacher_summaries_filtered_by_lesson_date(self):
        current_participant = self.complete_lesson_with_finance_docs(self.lesson)
        mark_parent_charge_paid(
            user=self.admin_user,
            charge=current_participant.parent_charge,
        )

        old_lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.now() - timedelta(days=10),
        )
        self.complete_lesson_with_finance_docs(old_lesson)

        today = timezone.localdate().isoformat()
        self.client.force_authenticate(self.admin_user)

        response = self.client.get('/api/my/payments/', {'date_from': today, 'date_to': today})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['charges']), 1)
        self.assertEqual(len(response.data['payouts']), 1)
        self.assertEqual(len(response.data['student_summaries']), 1)
        self.assertEqual(len(response.data['teacher_summaries']), 1)

        student_summary = response.data['student_summaries'][0]
        self.assertEqual(student_summary['student'], self.student.id)
        self.assertEqual(student_summary['charged_amount'], '600.00')
        self.assertEqual(student_summary['paid_amount'], '600.00')
        self.assertEqual(student_summary['debt_amount'], '0.00')

        teacher_summary = response.data['teacher_summaries'][0]
        self.assertEqual(teacher_summary['teacher'], self.teacher.id)
        self.assertEqual(teacher_summary['accrued_amount'], '350.00')
        self.assertEqual(teacher_summary['paid_amount'], '0.00')
        self.assertEqual(teacher_summary['debt_amount'], '350.00')

        payout = response.data['payouts'][0]
        self.assertEqual(payout['lesson'], self.lesson.id)
        self.assertEqual(payout['student_name'], self.student.user.telegram_username)

        student_filtered_response = self.client.get('/api/my/payments/', {'student': self.student.id})
        self.assertEqual(student_filtered_response.status_code, 200)
        self.assertEqual(len(student_filtered_response.data['charges']), 2)
        self.assertEqual(len(student_filtered_response.data['student_summaries']), 1)

        teacher_filtered_response = self.client.get('/api/my/payments/', {'teacher': self.teacher.id})
        self.assertEqual(teacher_filtered_response.status_code, 200)
        self.assertEqual(len(teacher_filtered_response.data['payouts']), 2)
        self.assertEqual(len(teacher_filtered_response.data['teacher_summaries']), 1)

    def test_admin_can_create_student_and_teacher_payments(self):
        self.client.force_authenticate(self.admin_user)
        today = timezone.localdate().isoformat()

        student_response = self.client.post(
            '/api/finance/student-payments/',
            {'student': self.student.id, 'amount': '250.00', 'paid_at': today, 'comment': 'cash'},
            format='json',
        )
        teacher_response = self.client.post(
            '/api/finance/teacher-payments/',
            {'teacher': self.teacher.id, 'amount': '175.00', 'paid_at': today, 'comment': 'card'},
            format='json',
        )

        self.assertEqual(student_response.status_code, 201)
        self.assertEqual(student_response.data['student'], self.student.id)
        self.assertEqual(student_response.data['amount'], '250.00')
        self.assertEqual(student_response.data['paid_at'], today)
        self.assertEqual(teacher_response.status_code, 201)
        self.assertEqual(teacher_response.data['teacher'], self.teacher.id)
        self.assertEqual(teacher_response.data['amount'], '175.00')
        self.assertEqual(teacher_response.data['paid_at'], today)

    def test_admin_teacher_summary_debt_count_uses_entered_teacher_payments(self):
        first_participant = self.complete_lesson_with_finance_docs(self.lesson)
        second_lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.now() + timedelta(hours=1),
        )
        second_participant = self.complete_lesson_with_finance_docs(second_lesson)
        TeacherPayment.objects.create(
            teacher=self.teacher,
            amount=first_participant.teacher_payout.amount + second_participant.teacher_payout.amount,
            paid_at=timezone.localdate(),
            created_by=self.admin_user,
        )
        self.client.force_authenticate(self.admin_user)

        response = self.client.get('/api/my/payments/')

        self.assertEqual(response.status_code, 200)
        teacher_summary = response.data['teacher_summaries'][0]
        self.assertEqual(teacher_summary['paid_amount'], teacher_summary['accrued_amount'])
        self.assertEqual(teacher_summary['debt_amount'], '0.00')
        self.assertEqual(teacher_summary['paid_count'], 2)
        self.assertEqual(teacher_summary['debt_count'], 0)

    def test_prepaid_completed_lesson_does_not_notify_student_or_parent_about_payment(self):
        StudentPayment.objects.create(
            student=self.student,
            amount='600.00',
            paid_at=timezone.localdate(),
            created_by=self.admin_user,
        )
        participant = self.complete_lesson_with_finance_docs(self.lesson)
        payment_notification_id = f'payment:{participant.parent_charge.id}'

        self.client.force_authenticate(self.student_user)
        student_response = self.client.get('/api/my/notifications/')

        self.client.force_authenticate(self.parent_user)
        parent_response = self.client.get('/api/my/notifications/')

        self.assertEqual(student_response.status_code, 200)
        self.assertEqual(parent_response.status_code, 200)
        self.assertFalse(any(item['id'] == payment_notification_id for item in student_response.data))
        self.assertFalse(any(item['id'] == payment_notification_id for item in parent_response.data))

    def test_partly_prepaid_completed_lesson_still_notifies_student_and_parent_about_payment(self):
        StudentPayment.objects.create(
            student=self.student,
            amount='500.00',
            paid_at=timezone.localdate(),
            created_by=self.admin_user,
        )
        participant = self.complete_lesson_with_finance_docs(self.lesson)
        payment_notification_id = f'payment:{participant.parent_charge.id}'

        self.client.force_authenticate(self.student_user)
        student_response = self.client.get('/api/my/notifications/')

        self.client.force_authenticate(self.parent_user)
        parent_response = self.client.get('/api/my/notifications/')

        self.assertEqual(student_response.status_code, 200)
        self.assertEqual(parent_response.status_code, 200)
        self.assertTrue(any(item['id'] == payment_notification_id for item in student_response.data))
        self.assertTrue(any(item['id'] == payment_notification_id for item in parent_response.data))

    def test_teacher_gets_notification_for_received_payment(self):
        payment = TeacherPayment.objects.create(
            teacher=self.teacher,
            amount='175.00',
            paid_at=timezone.localdate(),
            created_by=self.admin_user,
        )
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get('/api/my/notifications/')

        self.assertEqual(response.status_code, 200)
        payment_notifications = [item for item in response.data if item['id'] == f'teacher_payment:{payment.id}']
        self.assertEqual(len(payment_notifications), 1)
        self.assertEqual(payment_notifications[0]['title'], 'Надійшла виплата')
        self.assertEqual(payment_notifications[0]['url'], '/my/payments')

    def test_staff_teacher_does_not_get_teacher_payment_notification(self):
        self.teacher_user.is_staff = True
        self.teacher_user.save(update_fields=['is_staff'])
        payment = TeacherPayment.objects.create(
            teacher=self.teacher,
            amount='175.00',
            paid_at=timezone.localdate(),
            created_by=self.admin_user,
        )
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get('/api/my/notifications/')

        self.assertEqual(response.status_code, 200)
        payment_notifications = [item for item in response.data if item['id'] == f'teacher_payment:{payment.id}']
        self.assertEqual(payment_notifications, [])

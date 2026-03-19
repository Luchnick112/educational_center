from datetime import datetime

from django.utils.timezone import make_aware
from rest_framework import exceptions

from finance.models import ChargeStatus, PayoutStatus
from finance.services import (
    approve_teacher_payout,
    issue_parent_charge,
    mark_parent_charge_paid,
    mark_teacher_payout_paid,
)
from academics.models import AttendanceStatus
from academics.services import complete_lesson
from academics.tests.base import AcademicBaseTestCase
from users.models import User, UserRole


class FinanceServicesTestCase(AcademicBaseTestCase):
    def setUp(self):
        super().setUp()
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        complete_lesson(user=self.teacher_user, lesson=self.lesson, notes='Create finance docs')
        self.charge = self.lesson.participants.get().parent_charge
        self.payout = self.lesson.participants.get().teacher_payout
        self.admin_user = User.objects.create_user(
            username='service_admin',
            email='service_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )

    def test_issue_parent_charge_updates_status_and_due_date(self):
        due_date = datetime(2026, 3, 31)
        charge = issue_parent_charge(user=self.admin_user, charge=self.charge, due_date=due_date.date())

        self.assertEqual(charge.status, ChargeStatus.ISSUED)
        self.assertEqual(str(charge.due_date), '2026-03-31')

    def test_mark_parent_charge_paid_sets_paid_timestamp(self):
        paid_at = make_aware(datetime(2026, 3, 20, 10, 30))
        charge = mark_parent_charge_paid(user=self.admin_user, charge=self.charge, paid_at=paid_at)

        self.assertEqual(charge.status, ChargeStatus.PAID)
        self.assertEqual(charge.paid_at, paid_at)

    def test_approve_teacher_payout_sets_status(self):
        payout = approve_teacher_payout(user=self.admin_user, payout=self.payout)

        self.assertEqual(payout.status, PayoutStatus.APPROVED)
        self.assertIsNotNone(payout.approved_at)

    def test_mark_teacher_payout_paid_sets_paid_and_approval(self):
        paid_at = make_aware(datetime(2026, 3, 21, 9, 0))
        payout = mark_teacher_payout_paid(user=self.admin_user, payout=self.payout, paid_at=paid_at)

        self.assertEqual(payout.status, PayoutStatus.PAID)
        self.assertEqual(payout.paid_at, paid_at)
        self.assertIsNotNone(payout.approved_at)

    def test_finance_services_require_admin(self):
        with self.assertRaises(exceptions.PermissionDenied):
            issue_parent_charge(user=self.teacher_user, charge=self.charge)

        with self.assertRaises(exceptions.PermissionDenied):
            approve_teacher_payout(user=self.teacher_user, payout=self.payout)

    def test_cannot_issue_non_draft_charge(self):
        self.charge.status = ChargeStatus.ISSUED
        self.charge.save(update_fields=['status'])

        with self.assertRaises(exceptions.ValidationError):
            issue_parent_charge(user=self.admin_user, charge=self.charge)

    def test_cannot_approve_non_draft_payout(self):
        self.payout.status = PayoutStatus.APPROVED
        self.payout.save(update_fields=['status'])

        with self.assertRaises(exceptions.ValidationError):
            approve_teacher_payout(user=self.admin_user, payout=self.payout)

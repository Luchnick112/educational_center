from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from finance.models import LessonTeacherPayout, ParentCharge, PayoutStatus, TeacherPayout
from users.models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, User, UserRole

from academics.models import (
    AttendanceStatus,
    GroupAttendanceRate,
    Lesson,
    LessonStatus,
    StudentEnrollment,
    StudyGroup,
    StudyGroupFormat,
    Subject,
)


class LessonSignalsTestCase(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@example.com',
            password='pass12345',
            role=UserRole.TEACHER,
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user, hourly_rate=300)

        self.student_user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        self.student = StudentProfile.objects.create(user=self.student_user)

        self.parent_user = User.objects.create_user(
            username='parent1',
            email='parent1@example.com',
            password='pass12345',
            role=UserRole.PARENT,
        )
        self.parent = ParentProfile.objects.create(user=self.parent_user)
        StudentParentRelation.objects.create(
            parent=self.parent,
            student=self.student,
            is_primary=True,
            is_financial_contact=True,
        )

        self.subject = Subject.objects.create(name='Math')
        self.group = StudyGroup.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            format='group',
            capacity=8,
            student_price=500,
            teacher_rate=250,
        )
        self.enrollment = StudentEnrollment.objects.create(
            group=self.group,
            student=self.student,
            start_date=date.today(),
        )

    def create_completed_lesson(self, *, days_offset: int, attendance_status=AttendanceStatus.PRESENT):
        lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.now() - timedelta(days=20 - days_offset),
        )
        lesson.participants.update(attendance_status=attendance_status)
        lesson.status = LessonStatus.COMPLETED
        lesson.save(update_fields=['status'])
        return lesson

    def test_lesson_creation_builds_participants_without_confirmation_requests(self):
        lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.now(),
        )

        participant = lesson.participants.get()

        self.assertEqual(participant.student, self.student)
        self.assertFalse(participant.confirmations.exists())

    def test_lesson_creation_uses_student_lesson_price(self):
        self.student.lesson_price = Decimal('725.00')
        self.student.save(update_fields=['lesson_price'])

        lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.now(),
        )

        participant = lesson.participants.get()

        self.assertEqual(participant.billed_amount, self.student.lesson_price)

    def test_completed_individual_lesson_creates_parent_charge_and_teacher_payout_immediately(self):
        self.group.format = StudyGroupFormat.INDIVIDUAL
        self.group.save(update_fields=['format'])

        lesson = self.create_completed_lesson(days_offset=0)
        participant = lesson.participants.get()

        charge = ParentCharge.objects.get(participant=participant)
        payout = TeacherPayout.objects.get(participant=participant)

        self.assertEqual(charge.parent, self.parent)
        self.assertEqual(charge.amount, Decimal('500.00'))
        self.assertEqual(charge.lesson_count, 1)
        self.assertEqual(charge.billing_period, 1)
        self.assertEqual(payout.teacher, self.teacher)
        self.assertEqual(payout.amount, Decimal('250.00'))
        self.assertEqual(payout.lesson_count, 1)

    def test_completed_group_lessons_create_single_teacher_payout_after_tenth_lesson(self):
        second_student_user = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        second_student = StudentProfile.objects.create(user=second_student_user)
        StudentEnrollment.objects.create(
            group=self.group,
            student=second_student,
            start_date=date.today(),
        )
        GroupAttendanceRate.objects.create(
            group=self.group,
            present_count=1,
            teacher_rate=Decimal('250.00'),
            effective_from=timezone.now() - timedelta(days=30),
        )
        GroupAttendanceRate.objects.create(
            group=self.group,
            present_count=2,
            teacher_rate=Decimal('450.00'),
            effective_from=timezone.now() - timedelta(days=30),
        )

        for index in range(9):
            self.create_completed_lesson(days_offset=index)

        self.assertFalse(ParentCharge.objects.exists())
        self.assertFalse(LessonTeacherPayout.objects.exists())

        lesson = self.create_completed_lesson(days_offset=9)

        payout = LessonTeacherPayout.objects.get(lesson=lesson)

        self.assertEqual(ParentCharge.objects.filter(participant__lesson=lesson).count(), 1)
        self.assertFalse(TeacherPayout.objects.filter(participant__lesson=lesson).exists())
        self.assertEqual(payout.teacher, self.teacher)
        self.assertEqual(payout.amount, Decimal('4500.00'))
        self.assertEqual(payout.lesson_count, 10)

    def test_attendance_rate_change_recalculates_draft_group_lesson_payout(self):
        lesson = self.create_completed_lesson(days_offset=0)
        payout = LessonTeacherPayout.objects.create(
            lesson=lesson,
            teacher=self.teacher,
            amount=Decimal('0.00'),
        )

        GroupAttendanceRate.objects.create(
            group=self.group,
            present_count=1,
            teacher_rate=Decimal('550.00'),
            effective_from=lesson.starts_at - timedelta(days=1),
        )

        payout.refresh_from_db()

        self.assertEqual(payout.amount, Decimal('550.00'))

    def test_attendance_rate_change_does_not_recalculate_paid_group_lesson_payout(self):
        lesson = self.create_completed_lesson(days_offset=0)
        payout = LessonTeacherPayout.objects.create(
            lesson=lesson,
            teacher=self.teacher,
            amount=Decimal('0.00'),
            status=PayoutStatus.PAID,
        )

        GroupAttendanceRate.objects.create(
            group=self.group,
            present_count=1,
            teacher_rate=Decimal('550.00'),
            effective_from=lesson.starts_at - timedelta(days=1),
        )

        payout.refresh_from_db()

        self.assertEqual(payout.amount, Decimal('0.00'))

    def test_absent_student_is_still_charged_after_tenth_completed_lesson(self):
        for index in range(10):
            self.create_completed_lesson(days_offset=index, attendance_status=AttendanceStatus.ABSENT)

        charge = ParentCharge.objects.get()

        self.assertEqual(charge.student, self.student)
        self.assertEqual(charge.amount, Decimal('5000.00'))
        self.assertEqual(charge.lesson_count, 10)

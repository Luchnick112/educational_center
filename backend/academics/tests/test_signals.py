from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from finance.models import LessonTeacherPayout, ParentCharge, TeacherPayout
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

    def test_completed_individual_lesson_creates_parent_charge_and_teacher_payout(self):
        self.group.format = StudyGroupFormat.INDIVIDUAL
        self.group.save(update_fields=['format'])
        lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.now(),
        )
        participant = lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])

        lesson.status = LessonStatus.COMPLETED
        lesson.save()

        charge = ParentCharge.objects.get(participant=participant)
        payout = TeacherPayout.objects.get(participant=participant)

        self.assertEqual(charge.parent, self.parent)
        self.assertEqual(charge.amount, participant.billed_amount)
        self.assertEqual(payout.teacher, self.teacher)
        self.assertEqual(payout.amount, participant.payroll_amount)

    def test_completed_group_lesson_creates_single_lesson_teacher_payout_from_attendance_rate(self):
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
            effective_from=timezone.now() - timedelta(days=1),
        )
        GroupAttendanceRate.objects.create(
            group=self.group,
            present_count=2,
            teacher_rate=Decimal('450.00'),
            effective_from=timezone.now() - timedelta(days=1),
        )
        lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.now(),
        )
        lesson.participants.update(attendance_status=AttendanceStatus.PRESENT)

        lesson.status = LessonStatus.COMPLETED
        lesson.save()

        payout = LessonTeacherPayout.objects.get(lesson=lesson)

        self.assertEqual(ParentCharge.objects.filter(participant__lesson=lesson).count(), 1)
        self.assertFalse(TeacherPayout.objects.filter(participant__lesson=lesson).exists())
        self.assertEqual(payout.teacher, self.teacher)
        self.assertEqual(payout.amount, Decimal('450.00'))

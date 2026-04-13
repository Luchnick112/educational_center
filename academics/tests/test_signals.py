from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from finance.models import ParentCharge, TeacherPayout
from users.models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, User, UserRole

from academics.models import ConfirmationRequester, Lesson, LessonStatus, StudentEnrollment, StudyGroup, Subject


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
        self.student = StudentProfile.objects.create(user=self.student_user, grade='7')

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
            name='Math A',
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

    def test_lesson_creation_builds_participants_and_confirmations(self):
        lesson = Lesson.objects.create(
            group=self.group,
            title='Algebra',
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
        )

        participant = lesson.participants.get()
        confirmations = set(participant.confirmations.values_list('requested_from', flat=True))

        self.assertEqual(participant.student, self.student)
        self.assertEqual(confirmations, {
            ConfirmationRequester.STUDENT,
            ConfirmationRequester.PARENT,
            ConfirmationRequester.TEACHER,
        })

    def test_completed_lesson_creates_parent_charge_and_teacher_payout(self):
        lesson = Lesson.objects.create(
            group=self.group,
            title='Geometry',
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
        )

        lesson.status = LessonStatus.COMPLETED
        lesson.save()

        participant = lesson.participants.get()
        charge = ParentCharge.objects.get(participant=participant)
        payout = TeacherPayout.objects.get(participant=participant)

        self.assertEqual(charge.parent, self.parent)
        self.assertEqual(charge.amount, participant.billed_amount)
        self.assertEqual(payout.teacher, self.teacher)
        self.assertEqual(payout.amount, participant.payroll_amount)

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, User, UserRole

from academics.models import Lesson, StudentEnrollment, StudyGroup, Subject


class AcademicBaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.teacher_user = User.objects.create_user(
            username='teacher_api',
            telegram_username='@teacher_api',
            email='teacher_api@example.com',
            password='pass12345',
            role=UserRole.TEACHER,
        )
        self.teacher = TeacherProfile.objects.create(user=self.teacher_user, hourly_rate=300)

        self.student_user = User.objects.create_user(
            username='student_api',
            telegram_username='@student_api',
            email='student_api@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        self.student = StudentProfile.objects.create(user=self.student_user, grade='8')

        self.parent_user = User.objects.create_user(
            username='parent_api',
            telegram_username='@parent_api',
            email='parent_api@example.com',
            password='pass12345',
            role=UserRole.PARENT,
        )
        self.parent = ParentProfile.objects.create(user=self.parent_user)
        StudentParentRelation.objects.create(
            parent=self.parent,
            student=self.student,
            is_financial_contact=True,
        )

        self.subject = Subject.objects.create(name='Physics')
        self.group = StudyGroup.objects.create(
            subject=self.subject,
            teacher=self.teacher,
            format='group',
            capacity=10,
            student_price=600,
            teacher_rate=350,
        )
        self.enrollment = StudentEnrollment.objects.create(
            group=self.group,
            student=self.student,
            start_date=date.today(),
        )
        self.lesson = Lesson.objects.create(
            group=self.group,
            title='Mechanics',
            starts_at=timezone.now(),
            ends_at=timezone.now() + timedelta(hours=1),
        )

from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Lesson, LessonConfirmation, LessonParticipant, StudentEnrollment, StudyGroup, Subject
from finance.models import ParentCharge, TeacherPayout
from users.models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, TelegramLinkToken, User, UserRole


class DemoFixtureTestCase(TestCase):
    fixtures = ['demo_data.json']

    def test_demo_fixture_loads_without_duplicate_signal_side_effects(self):
        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(TeacherProfile.objects.count(), 1)
        self.assertEqual(StudentProfile.objects.count(), 1)
        self.assertEqual(ParentProfile.objects.count(), 1)
        self.assertEqual(Subject.objects.count(), 1)
        self.assertEqual(StudyGroup.objects.count(), 1)
        self.assertEqual(StudentEnrollment.objects.count(), 1)
        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(LessonParticipant.objects.count(), 1)
        self.assertEqual(LessonConfirmation.objects.count(), 3)
        self.assertEqual(ParentCharge.objects.count(), 1)
        self.assertEqual(TeacherPayout.objects.count(), 1)

    def test_demo_fixture_uses_email_credentials(self):
        teacher = User.objects.get(email='teacher@example.com')
        student = User.objects.get(email='student@example.com')

        self.assertEqual(teacher.role, 'teacher')
        self.assertEqual(student.student_profile.grade, '8')


class TelegramLinkFlowTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='u1',
            telegram_username='@u1_user',
            password='pass12345',
            role=UserRole.TEACHER,
        )

    def test_can_generate_link_token_and_link_chat_id_via_webhook(self):
        self.client.force_authenticate(self.user)

        token_response = self.client.post('/api/users/telegram/link-token/')
        self.assertEqual(token_response.status_code, 200)
        token = token_response.data['token']
        self.assertTrue(TelegramLinkToken.objects.filter(user=self.user, token=token).exists())

        webhook_response = self.client.post(
            '/api/users/telegram/webhook/',
            data={
                'update_id': 1,
                'message': {
                    'message_id': 10,
                    'chat': {'id': 123456},
                    'from': {'id': 654321, 'username': 'SomeUser'},
                    'text': f'/start {token}',
                },
            },
            format='json',
        )
        self.assertEqual(webhook_response.status_code, 200)

        self.user.refresh_from_db()
        self.assertEqual(self.user.telegram_chat_id, 123456)
        self.assertEqual(self.user.telegram_user_id, 654321)


class StudentParentRelationApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff = User.objects.create_user(
            username='staff_user',
            telegram_username='@staff_user',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.parent_user = User.objects.create_user(
            username='parent_user',
            telegram_username='@parent_user',
            password='pass12345',
            role=UserRole.PARENT,
        )
        self.student_user = User.objects.create_user(
            username='student_user',
            telegram_username='@student_user',
            password='pass12345',
            role=UserRole.STUDENT,
        )

        self.parent = ParentProfile.objects.create(user=self.parent_user)
        self.student = StudentProfile.objects.create(user=self.student_user)

    def test_staff_can_create_relation(self):
        self.client.force_authenticate(self.staff)
        resp = self.client.post(
            '/api/users/student-parent-relations/',
            {
                'parent': self.parent.id,
                'student': self.student.id,
                'is_primary': True,
                'is_financial_contact': True,
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertTrue(
            StudentParentRelation.objects.filter(parent=self.parent, student=self.student).exists()
        )

    def test_non_staff_cannot_create_relation(self):
        self.client.force_authenticate(self.parent_user)
        resp = self.client.post(
            '/api/users/student-parent-relations/',
            {
                'parent': self.parent.id,
                'student': self.student.id,
                'is_primary': True,
                'is_financial_contact': True,
            },
            format='json',
        )
        self.assertEqual(resp.status_code, 403)

    def test_parent_sees_only_own_relations(self):
        other_parent_user = User.objects.create_user(
            username='parent_user2',
            telegram_username='@parent_user2',
            password='pass12345',
            role=UserRole.PARENT,
        )
        other_parent = ParentProfile.objects.create(user=other_parent_user)
        StudentParentRelation.objects.create(parent=self.parent, student=self.student)
        StudentParentRelation.objects.create(parent=other_parent, student=self.student)

        self.client.force_authenticate(self.parent_user)
        resp = self.client.get('/api/users/student-parent-relations/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['parent'], self.parent.id)

    def test_student_sees_only_own_relations(self):
        other_student_user = User.objects.create_user(
            username='student_user2',
            telegram_username='@student_user2',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        other_student = StudentProfile.objects.create(user=other_student_user)
        StudentParentRelation.objects.create(parent=self.parent, student=self.student)
        StudentParentRelation.objects.create(parent=self.parent, student=other_student)

        self.client.force_authenticate(self.student_user)
        resp = self.client.get('/api/users/student-parent-relations/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['student'], self.student.id)

    def test_parents_endpoint_user_detail_has_relationship_students_min_fields(self):
        self.student_user.first_name = 'Andrii'
        self.student_user.last_name = 'Student'
        self.student_user.telegram_username = '@stud_ex_21'
        self.student_user.save(update_fields=['first_name', 'last_name', 'telegram_username'])
        StudentParentRelation.objects.create(parent=self.parent, student=self.student)

        self.client.force_authenticate(self.parent_user)
        resp = self.client.get('/api/users/parents/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

        relationship = resp.data[0]['user_detail']['relationship']
        self.assertEqual(len(relationship), 1)
        self.assertEqual(
            relationship[0],
            {'first_name': 'Andrii', 'last_name': 'Student', 'telegram_username': '@stud_ex_21'},
        )

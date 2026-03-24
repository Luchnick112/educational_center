from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Lesson, LessonConfirmation, LessonParticipant, StudentEnrollment, StudyGroup, Subject
from finance.models import ParentCharge, TeacherPayout
from users.models import ParentProfile, StudentProfile, TeacherProfile, TelegramLinkToken, User, UserRole


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

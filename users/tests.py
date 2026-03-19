from django.test import TestCase

from academics.models import Lesson, LessonConfirmation, LessonParticipant, StudentEnrollment, StudyGroup, Subject
from finance.models import ParentCharge, TeacherPayout
from users.models import ParentProfile, StudentProfile, TeacherProfile, User


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

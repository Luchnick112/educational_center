from django.test import TestCase, override_settings
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
        self.assertTrue(hasattr(student, 'student_profile'))


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


class RegisterApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            username='staff_user',
            telegram_username='@staff_user',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )

    def test_staff_can_create_student_without_password(self):
        self.client.force_authenticate(self.staff)

        resp = self.client.post(
            '/api/users/register/',
            {
                'first_name': 'Ivan',
                'last_name': 'Student',
                'telegram_username': '@ivan_student',
                'email': 'ivan.student@example.com',
                'role': UserRole.STUDENT,
                'phone': '+380000000010',
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(pk=resp.data['id'])
        self.assertEqual(user.role, UserRole.STUDENT)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(hasattr(user, 'student_profile'))

    def test_staff_can_create_parent_and_teacher_without_password(self):
        self.client.force_authenticate(self.staff)

        cases = (
            (UserRole.PARENT, '@parent_without_password', 'parent_profile'),
            (UserRole.TEACHER, '@teacher_without_password', 'teacher_profile'),
        )
        for role, telegram_username, profile_attr in cases:
            with self.subTest(role=role):
                resp = self.client.post(
                    '/api/users/register/',
                    {
                        'first_name': role.title(),
                        'last_name': 'User',
                        'telegram_username': telegram_username,
                        'role': role,
                    },
                    format='json',
                )

                self.assertEqual(resp.status_code, 201, resp.data)
                user = User.objects.get(pk=resp.data['id'])
                self.assertEqual(user.role, role)
                self.assertFalse(user.has_usable_password())
                self.assertTrue(hasattr(user, profile_attr))

    def test_staff_can_create_user_with_phone_only(self):
        self.client.force_authenticate(self.staff)

        resp = self.client.post(
            '/api/users/register/',
            {
                'first_name': 'Phone',
                'last_name': 'Only',
                'phone': '+380501112233',
                'role': UserRole.TEACHER,
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(pk=resp.data['id'])
        self.assertEqual(user.phone, '+380501112233')
        self.assertEqual(user.role, UserRole.TEACHER)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(hasattr(user, 'teacher_profile'))

    def test_staff_can_update_student_lesson_price(self):
        self.client.force_authenticate(self.staff)
        student_user = User.objects.create_user(
            username='priced_student',
            telegram_username='@priced_student',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        student = StudentProfile.objects.create(user=student_user)

        resp = self.client.patch(
            f'/api/users/students/{student.id}/',
            {
                'lesson_price': '750.00',
                'notes': 'Individual lesson price',
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        student.refresh_from_db()
        self.assertEqual(student.lesson_price, 750)
        self.assertEqual(student.notes, 'Individual lesson price')

    def test_student_can_claim_staff_created_account_by_telegram(self):
        student = User.objects.create(
            username='@claim_student',
            telegram_username='@claim_student',
            email='claim.student@example.com',
            role=UserRole.STUDENT,
        )
        student.set_unusable_password()
        student.save()
        StudentProfile.objects.create(user=student)

        resp = self.client.post(
            '/api/users/register/',
            {
                'first_name': 'Claimed',
                'last_name': 'Student',
                'telegram_username': '@claim_student',
                'role': UserRole.STUDENT,
                'password': 'newpass123',
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['id'], student.id)

        student.refresh_from_db()
        self.assertTrue(student.has_usable_password())
        self.assertTrue(student.check_password('newpass123'))
        self.assertEqual(student.first_name, 'Claimed')

        token_resp = self.client.post(
            '/api/users/token/',
            {'telegram_username': '@claim_student', 'password': 'newpass123'},
            format='json',
        )
        self.assertEqual(token_resp.status_code, 200, token_resp.data)

    def test_teacher_can_claim_staff_created_account_by_telegram(self):
        teacher = User.objects.create(
            username='@step_1b',
            telegram_username='@step_1b',
            email='',
            role=UserRole.TEACHER,
            is_active=True,
        )
        teacher.set_unusable_password()
        teacher.save()
        TeacherProfile.objects.create(user=teacher)

        resp = self.client.post(
            '/api/users/register/',
            {
                'first_name': 'Viktor',
                'last_name': 'Malolaykov',
                'telegram_username': '@step_1b',
                'role': UserRole.TEACHER,
                'password': 'newpass123',
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data['id'], teacher.id)

        teacher.refresh_from_db()
        self.assertTrue(teacher.is_active)
        self.assertTrue(teacher.has_usable_password())
        self.assertTrue(teacher.check_password('newpass123'))
        self.assertEqual(teacher.first_name, 'Viktor')

        token_resp = self.client.post(
            '/api/users/token/',
            {'telegram_username': '@step_1b', 'password': 'newpass123'},
            format='json',
        )
        self.assertEqual(token_resp.status_code, 200, token_resp.data)

    @override_settings(DEFAULT_PHONE_COUNTRY_CODE='380')
    def test_token_login_accepts_telegram_email_or_phone(self):
        user = User.objects.create_user(
            username='multi_login',
            telegram_username='@multi_login',
            email='multi.login@example.com',
            phone='+380 50 111-22-33',
            password='pass12345',
            role=UserRole.TEACHER,
        )
        TeacherProfile.objects.create(user=user)

        for login in ('@multi_login', 'multi.login@example.com', '+380501112233', '380 50 111 22 33', '0501112233'):
            with self.subTest(login=login):
                resp = self.client.post(
                    '/api/users/token/',
                    {'login': login, 'password': 'pass12345'},
                    format='json',
                )
                self.assertEqual(resp.status_code, 200, resp.data)
                self.assertIn('access', resp.data)

    def test_token_login_rejects_ambiguous_phone(self):
        for suffix in ('one', 'two'):
            User.objects.create_user(
                username=f'phone_{suffix}',
                telegram_username=f'@phone_{suffix}',
                phone='+380501112233',
                password='pass12345',
                role=UserRole.TEACHER,
            )

        resp = self.client.post(
            '/api/users/token/',
            {'login': '+380501112233', 'password': 'pass12345'},
            format='json',
        )

        self.assertEqual(resp.status_code, 400)

    def test_public_registration_rejects_existing_usable_account(self):
        User.objects.create_user(
            username='@existing_student',
            telegram_username='@existing_student',
            password='pass12345',
            role=UserRole.STUDENT,
        )

        resp = self.client.post(
            '/api/users/register/',
            {
                'first_name': 'Existing',
                'last_name': 'Student',
                'telegram_username': '@existing_student',
                'role': UserRole.STUDENT,
                'password': 'newpass123',
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 400)

    def test_staff_can_update_user_account_fields(self):
        self.client.force_authenticate(self.staff)
        student = User.objects.create_user(
            username='student_user',
            telegram_username='@student_user',
            email='old.student@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )

        resp = self.client.patch(
            f'/api/users/{student.id}/',
            {
                'first_name': 'Updated',
                'last_name': 'Student',
                'telegram_username': 'UpdatedStudent',
                'email': 'UPDATED.STUDENT@EXAMPLE.COM',
                'phone': '+380000000011',
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        student.refresh_from_db()
        self.assertEqual(student.first_name, 'Updated')
        self.assertEqual(student.last_name, 'Student')
        self.assertEqual(student.telegram_username, '@updatedstudent')
        self.assertEqual(student.email, 'updated.student@example.com')
        self.assertEqual(student.phone, '+380000000011')

    def test_user_can_update_own_account_fields(self):
        user = User.objects.create_user(
            username='own_user',
            telegram_username='@own_user',
            email='own.old@example.com',
            phone='+380000000012',
            password='pass12345',
            role=UserRole.TEACHER,
        )
        self.client.force_authenticate(user)

        resp = self.client.patch(
            '/api/users/me/',
            {
                'first_name': 'Own',
                'last_name': 'Updated',
                'telegram_username': '@own_updated',
                'email': 'own.updated@example.com',
                'phone': '+380000000013',
            },
            format='json',
        )

        self.assertEqual(resp.status_code, 200, resp.data)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Own')
        self.assertEqual(user.last_name, 'Updated')
        self.assertEqual(user.telegram_username, '@own_updated')
        self.assertEqual(user.email, 'own.updated@example.com')
        self.assertEqual(user.phone, '+380000000013')

    def test_admin_dashboard_includes_active_student_and_teacher_counts(self):
        active_student_user = User.objects.create_user(
            username='active_student',
            telegram_username='@active_student',
            role=UserRole.STUDENT,
        )
        inactive_student_user = User.objects.create_user(
            username='inactive_student',
            telegram_username='@inactive_student',
            role=UserRole.STUDENT,
            is_active=False,
        )
        active_teacher_user = User.objects.create_user(
            username='active_teacher',
            telegram_username='@active_teacher',
            role=UserRole.TEACHER,
        )
        inactive_teacher_user = User.objects.create_user(
            username='inactive_teacher',
            telegram_username='@inactive_teacher',
            role=UserRole.TEACHER,
            is_active=False,
        )
        StudentProfile.objects.create(user=active_student_user)
        StudentProfile.objects.create(user=inactive_student_user)
        TeacherProfile.objects.create(user=active_teacher_user)
        TeacherProfile.objects.create(user=inactive_teacher_user)

        self.client.force_authenticate(self.staff)
        resp = self.client.get('/api/users/dashboard/')

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data['stats']['Студенти'], 1)
        self.assertEqual(resp.data['stats']['Вчителі'], 1)

    def test_staff_delete_student_profile_deactivates_user(self):
        self.client.force_authenticate(self.staff)
        student_user = User.objects.create_user(
            username='step1_b',
            telegram_username='@step1_b',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        student = StudentProfile.objects.create(user=student_user)

        resp = self.client.delete(f'/api/users/students/{student.id}/')

        self.assertEqual(resp.status_code, 204, resp.data)
        student_user.refresh_from_db()
        self.assertFalse(student_user.is_active)

        list_resp = self.client.get('/api/users/students/')
        self.assertEqual(list_resp.status_code, 200, list_resp.data)
        self.assertNotIn(student.id, [item['id'] for item in list_resp.data])

        token_client = APIClient()
        token_resp = token_client.post(
            '/api/users/token/',
            {'telegram_username': '@step1_b', 'password': 'pass12345'},
            format='json',
        )
        self.assertEqual(token_resp.status_code, 400)


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

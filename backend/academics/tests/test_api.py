from decimal import Decimal
from datetime import datetime, timedelta

from django.utils import timezone
from finance.models import ChargeStatus, ParentCharge, PayoutStatus, TeacherPayout
from rest_framework.test import APIRequestFactory
from users.models import ParentProfile, StudentProfile, TeacherProfile, User, UserRole

from academics.models import (
    AttendanceStatus,
    ConfirmationRequester,
    GroupPricing,
    Lesson,
    LessonConfirmation,
    LessonParticipant,
    LessonRescheduleStatus,
    LessonStatus,
    StudentEnrollment,
)
from academics.models import StudyGroup, Subject
from academics.serializers import LessonSerializer
from academics.tests.base import AcademicBaseTestCase


class RoleAwareApiTestCase(AcademicBaseTestCase):
    def test_register_page_is_available_in_browser(self):
        response = self.client.get('/api/users/register/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create a new account')

    def test_token_page_is_available_in_browser(self):
        response = self.client.get('/api/users/token/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Get access tokens')

    def test_token_refresh_page_is_available_in_browser(self):
        response = self.client.get('/api/users/token/refresh/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Refresh access token')

    def test_group_name_is_auto_generated_on_create(self):
        admin_user = User.objects.create_user(
            username='group_admin',
            email='group_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        create_response = self.client.post(
            '/api/academics/groups/',
            {
                'subject': self.subject.id,
                'teacher': self.teacher.id,
                'capacity': 5,
                'student_price': '700.00',
                'teacher_rate': '400.00',
                'is_active': True,
            },
            format='json',
        )

        self.assertEqual(create_response.status_code, 201)
        created_id = create_response.data['id']
        self.assertEqual(create_response.data['name'], f'{self.subject.name}{self.teacher.id}{created_id}')

    def test_teacher_can_create_group_without_teacher_or_prices(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.post(
            '/api/academics/groups/',
            {
                'subject': self.subject.id,
                'capacity': 5,
                'is_active': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['teacher'], self.teacher.id)
        self.assertEqual(response.data['teacher_rate'], '0.00')
        self.assertNotIn('student_price', response.data)

    def test_teacher_sees_only_teacher_rate_in_group_detail(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get(f'/api/academics/groups/{self.group.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('student_price', response.data)
        self.assertIn('teacher_rate', response.data)

    def test_teacher_sees_only_payroll_amount_in_lesson_participants(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get(f'/api/academics/lessons/{self.lesson.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('participants', response.data)
        self.assertEqual(len(response.data['participants']), 1)
        participant = response.data['participants'][0]
        self.assertNotIn('billed_amount', participant)
        self.assertIn('payroll_amount', participant)

    def test_teacher_my_lessons_include_lesson_payroll_amount(self):
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get('/api/my/lessons/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['payroll_amount'], '350.00')
        self.assertNotIn('billed_amount', response.data[0])

    def test_admin_my_lessons_include_lesson_billed_amount(self):
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        admin_user = User.objects.create_user(
            username='lesson_amount_admin',
            email='lesson_amount_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        response = self.client.get('/api/my/lessons/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['payroll_amount'], '350.00')
        self.assertEqual(response.data[0]['billed_amount'], '600.00')

    def test_admin_can_update_lesson_detail_and_participant_amounts(self):
        admin_user = User.objects.create_user(
            username='lesson_detail_admin',
            email='lesson_detail_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        starts_at = timezone.make_aware(datetime(2026, 5, 19, 12, 30))
        self.client.force_authenticate(admin_user)

        response = self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {
                'starts_at': starts_at.isoformat(),
                'status': LessonStatus.COMPLETED,
                'notes': 'Admin correction',
                'participant_updates': [
                    {
                        'id': participant.id,
                        'billed_amount': '650.00',
                        'payroll_amount': '375.00',
                    }
                ],
            },
            format='json',
        )

        self.lesson.refresh_from_db()
        participant.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.lesson.status, LessonStatus.COMPLETED)
        self.assertEqual(self.lesson.notes, 'Admin correction')
        self.assertEqual(participant.billed_amount, Decimal('650.00'))
        self.assertEqual(participant.payroll_amount, Decimal('375.00'))
        self.assertEqual(response.data['participants'][0]['billed_amount'], '650.00')
        self.assertEqual(response.data['participants'][0]['payroll_amount'], '375.00')
        self.assertEqual(ParentCharge.objects.get(participant=participant).amount, Decimal('650.00'))
        self.assertEqual(TeacherPayout.objects.get(participant=participant).amount, Decimal('375.00'))

    def test_student_my_lessons_hide_lesson_payroll_amount(self):
        self.client.force_authenticate(self.student_user)

        response = self.client.get('/api/my/lessons/')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('payroll_amount', response.data[0])
        self.assertNotIn('billed_amount', response.data[0])

    def test_student_lesson_detail_includes_only_own_participant(self):
        other_student_user = User.objects.create_user(
            username='other_student_lesson_detail',
            email='other_student_lesson_detail@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        other_student = StudentProfile.objects.create(user=other_student_user, grade='8')
        other_enrollment = StudentEnrollment.objects.create(
            group=self.group,
            student=other_student,
            start_date=timezone.localdate(),
        )
        LessonParticipant.objects.create(lesson=self.lesson, enrollment=other_enrollment)
        self.client.force_authenticate(self.student_user)

        response = self.client.get(f'/api/academics/lessons/{self.lesson.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['participants']), 1)
        self.assertEqual(response.data['participants'][0]['student'], self.student.id)
        self.assertIn('billed_amount', response.data['participants'][0])
        self.assertNotIn('payroll_amount', response.data['participants'][0])

    def test_parent_lesson_detail_includes_only_child_participants(self):
        other_student_user = User.objects.create_user(
            username='other_child_lesson_detail',
            email='other_child_lesson_detail@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        other_student = StudentProfile.objects.create(user=other_student_user, grade='8')
        other_enrollment = StudentEnrollment.objects.create(
            group=self.group,
            student=other_student,
            start_date=timezone.localdate(),
        )
        LessonParticipant.objects.create(lesson=self.lesson, enrollment=other_enrollment)
        self.client.force_authenticate(self.parent_user)

        response = self.client.get(f'/api/academics/lessons/{self.lesson.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['participants']), 1)
        self.assertEqual(response.data['participants'][0]['student'], self.student.id)
        self.assertIn('billed_amount', response.data['participants'][0])
        self.assertNotIn('payroll_amount', response.data['participants'][0])

    def test_my_lessons_can_be_filtered_by_date_interval(self):
        self.lesson.starts_at = timezone.make_aware(datetime(2026, 5, 10, 10, 0))
        self.lesson.save(update_fields=['starts_at'])
        outside_lesson = Lesson.objects.create(
            group=self.group,
            starts_at=timezone.make_aware(datetime(2026, 5, 20, 10, 0)),
        )
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get('/api/my/lessons/?date_from=2026-05-10&date_to=2026-05-10')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [self.lesson.id])
        self.assertNotIn(outside_lesson.id, [item['id'] for item in response.data])

    def test_student_sees_only_own_price_in_group_detail(self):
        self.enrollment.student_price_override = Decimal('123.45')
        self.enrollment.save(update_fields=['student_price_override'])
        self.client.force_authenticate(self.student_user)

        response = self.client.get(f'/api/academics/groups/{self.group.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('teacher_rate', response.data)
        self.assertEqual(response.data['student_price'], '123.45')

    def test_parent_sees_only_child_price_in_group_detail(self):
        self.enrollment.student_price_override = Decimal('234.56')
        self.enrollment.save(update_fields=['student_price_override'])
        self.client.force_authenticate(self.parent_user)

        response = self.client.get(f'/api/academics/groups/{self.group.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('teacher_rate', response.data)
        self.assertEqual(response.data['student_price'], '234.56')

    def test_student_me_and_my_lessons_endpoints(self):
        self.client.force_authenticate(self.student_user)

        me_response = self.client.get('/api/me/')
        lessons_response = self.client.get('/api/my/lessons/')
        payments_response = self.client.get('/api/my/payments/')

        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.data['role'], UserRole.STUDENT)
        self.assertIn('my', me_response.data)
        keys = {item['key'] for item in me_response.data['my']}
        self.assertEqual(
            keys,
            {'lessons', 'children', 'children_summary', 'payments', 'confirmations', 'notifications'},
        )
        self.assertEqual(lessons_response.status_code, 200)
        self.assertEqual(len(lessons_response.data), 1)
        self.assertEqual(payments_response.status_code, 200)

    def test_parent_sees_only_linked_children(self):
        self.client.force_authenticate(self.parent_user)

        children_response = self.client.get('/api/my/children/')
        confirmations_response = self.client.get('/api/my/confirmations/')

        self.assertEqual(children_response.status_code, 200)
        self.assertEqual(len(children_response.data), 1)
        self.assertEqual(children_response.data[0]['id'], self.student.id)
        self.assertEqual(confirmations_response.status_code, 200)

    def test_teacher_notifications_do_not_include_lesson_confirmations(self):
        other_student_user = User.objects.create_user(
            username='other_notification_student',
            email='other_notification_student@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        other_student = StudentProfile.objects.create(user=other_student_user, grade='8')
        other_enrollment = StudentEnrollment.objects.create(
            group=self.group,
            student=other_student,
            start_date=timezone.localdate(),
        )
        LessonParticipant.objects.create(lesson=self.lesson, enrollment=other_enrollment)
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get('/api/my/notifications/')

        self.assertEqual(response.status_code, 200)
        confirmation_notifications = [
            item for item in response.data
            if item['kind'] == 'confirmation'
        ]
        self.assertEqual(confirmation_notifications, [])

    def test_lessons_browsable_api_page_renders_for_html_requests(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.get('/api/academics/lessons/', HTTP_ACCEPT='text/html')

        self.assertEqual(response.status_code, 200)

    def test_browsable_api_pages_with_date_fields_render_for_html_requests(self):
        admin_user = User.objects.create_user(
            username='html_admin',
            email='html_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        urls = [
            '/api/academics/enrollments/',
            '/api/academics/confirmations/',
            '/api/finance/parent-charges/',
            '/api/finance/teacher-payouts/',
        ]

        for url in urls:
            response = self.client.get(url, HTTP_ACCEPT='text/html')
            self.assertEqual(response.status_code, 200, msg=url)

    def test_register_creates_user_and_role_profile(self):
        response = self.client.post(
            '/api/users/register/',
            {
                'password': 'pass12345',
                'first_name': 'New',
                'last_name': 'Teacher',
                'telegram_username': '@teacher_example',
                'role': UserRole.TEACHER,
                'phone': '+380001112233',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        created_user = User.objects.get(telegram_username='@teacher_example')
        self.assertTrue(hasattr(created_user, 'teacher_profile'))
        self.assertEqual(response.data['telegram_username'], '@teacher_example')

    def test_token_obtain_uses_telegram_username(self):
        response = self.client.post(
            '/api/users/token/',
            {
                'telegram_username': '@teacher_api',
                'password': 'pass12345',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_teacher_can_mark_attendance_and_complete_lesson(self):
        participant = self.lesson.participants.get()
        self.client.force_authenticate(self.teacher_user)

        attendance_response = self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/mark-attendance/',
            {
                'participant_id': participant.id,
                'attendance_status': AttendanceStatus.PRESENT,
            },
            format='json',
        )
        complete_response = self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/complete/',
            {'notes': 'Completed on time'},
            format='json',
        )

        self.lesson.refresh_from_db()
        participant.refresh_from_db()

        self.assertEqual(attendance_response.status_code, 200)
        self.assertEqual(participant.attendance_status, AttendanceStatus.PRESENT)
        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(self.lesson.status, LessonStatus.COMPLETED)
        self.assertTrue(ParentCharge.objects.filter(participant=participant).exists())
        self.assertTrue(TeacherPayout.objects.filter(participant=participant).exists())

    def test_teacher_can_create_and_update_own_schedule(self):
        self.client.force_authenticate(self.teacher_user)

        starts_at = timezone.now() + timedelta(days=1)

        create_response = self.client.post(
            '/api/academics/lessons/',
            {
                'group': self.group.id,
                'starts_at': starts_at.isoformat(),
                'notes': 'New schedule item',
            },
            format='json',
        )
        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data['group'], self.group.id)
        self.assertEqual(create_response.data['status'], LessonStatus.SCHEDULED)
        self.assertEqual(create_response.data['notes'], 'New schedule item')

        lesson_id = create_response.data['id']
        update_response = self.client.patch(
            f'/api/academics/lessons/{lesson_id}/',
            {'notes': 'Updated notes'},
            format='json',
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.data['notes'], 'Updated notes')

    def test_teacher_can_update_lesson_status_and_payroll_amount(self):
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        self.client.force_authenticate(self.teacher_user)

        response = self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {
                'status': LessonStatus.COMPLETED,
                'participant_updates': [
                    {
                        'id': participant.id,
                        'payroll_amount': '410.00',
                    }
                ],
            },
            format='json',
        )

        self.lesson.refresh_from_db()
        participant.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.lesson.status, LessonStatus.COMPLETED)
        self.assertEqual(participant.payroll_amount, Decimal('410.00'))
        self.assertEqual(participant.billed_amount, Decimal('600.00'))
        self.assertEqual(response.data['participants'][0]['payroll_amount'], '410.00')
        self.assertNotIn('billed_amount', response.data['participants'][0])

    def test_teacher_can_cancel_unpaid_lesson(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {'status': LessonStatus.CANCELLED},
            format='json',
        )

        self.lesson.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.lesson.status, LessonStatus.CANCELLED)

    def test_teacher_cannot_change_paid_lesson_status(self):
        participant = self.lesson.participants.get()
        self.client.force_authenticate(self.teacher_user)
        self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {'status': LessonStatus.COMPLETED},
            format='json',
        )
        charge = ParentCharge.objects.get(participant=participant)
        charge.status = ChargeStatus.PAID
        charge.paid_at = timezone.now()
        charge.save(update_fields=['status', 'paid_at'])

        response = self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {'status': LessonStatus.CANCELLED},
            format='json',
        )

        self.lesson.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.lesson.status, LessonStatus.COMPLETED)

    def test_teacher_notifications_ignore_draft_payouts(self):
        self.client.force_authenticate(self.teacher_user)
        self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {'status': LessonStatus.COMPLETED},
            format='json',
        )

        response = self.client.get('/api/my/notifications/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(any(item['kind'] == 'payout' for item in response.data))

    def test_teacher_cannot_update_billed_amount(self):
        participant = self.lesson.participants.get()
        self.client.force_authenticate(self.teacher_user)

        response = self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {
                'participant_updates': [
                    {
                        'id': participant.id,
                        'billed_amount': '999.00',
                    }
                ],
            },
            format='json',
        )

        participant.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(participant.billed_amount, Decimal('600.00'))

    def test_teacher_cannot_directly_reschedule_lesson(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.patch(
            f'/api/academics/lessons/{self.lesson.id}/',
            {'starts_at': (timezone.now() + timedelta(days=2)).isoformat()},
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_admin_can_manage_group_pricing_rules(self):
        admin_user = User.objects.create_user(
            username='pricing_admin',
            email='pricing_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        response = self.client.post(
            '/api/academics/group-pricings/',
            {
                'group': self.group.id,
                'student_price': '800.00',
                'teacher_rate': '420.00',
                'effective_from': timezone.make_aware(datetime(2026, 6, 1, 0, 0)).isoformat(),
            },
            format='json',
        )
        list_response = self.client.get(f'/api/academics/group-pricings/?group={self.group.id}')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['student_price'], '800.00')
        self.assertEqual(response.data['teacher_rate'], '420.00')
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertTrue(GroupPricing.objects.filter(group=self.group, student_price='800.00').exists())

    def test_teacher_cannot_manage_group_pricing_rules(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.post(
            '/api/academics/group-pricings/',
            {
                'group': self.group.id,
                'student_price': '800.00',
                'teacher_rate': '420.00',
                'effective_from': timezone.make_aware(datetime(2026, 6, 1, 0, 0)).isoformat(),
            },
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_create_lesson_for_other_teacher_group(self):
        other_teacher_user = User.objects.create_user(
            username='other_teacher_for_schedule',
            email='other_teacher_for_schedule@example.com',
            password='pass12345',
            role=UserRole.TEACHER,
        )
        other_teacher = TeacherProfile.objects.create(user=other_teacher_user, hourly_rate=200)
        other_subject = Subject.objects.create(name='Chemistry')
        other_group = StudyGroup.objects.create(
            subject=other_subject,
            teacher=other_teacher,
            format='group',
            capacity=10,
            student_price=600,
            teacher_rate=350,
        )

        self.client.force_authenticate(self.teacher_user)
        starts_at = timezone.now() + timedelta(days=1)

        response = self.client.post(
            '/api/academics/lessons/',
            {
                'group': other_group.id,
                'starts_at': starts_at.isoformat(),
                'notes': 'Should be forbidden',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_teacher_create_lesson_group_choices_are_limited_to_own_groups(self):
        other_teacher_user = User.objects.create_user(
            username='other_teacher_for_lesson_choices',
            email='other_teacher_for_lesson_choices@example.com',
            password='pass12345',
            role=UserRole.TEACHER,
        )
        other_teacher = TeacherProfile.objects.create(user=other_teacher_user, hourly_rate=200)
        other_subject = Subject.objects.create(name='Biology')
        other_group = StudyGroup.objects.create(
            subject=other_subject,
            teacher=other_teacher,
            format='group',
            capacity=10,
            student_price=600,
            teacher_rate=350,
        )

        factory = APIRequestFactory()
        request = factory.post('/api/academics/lessons/', {}, format='json')
        request.user = self.teacher_user

        serializer = LessonSerializer(context={'request': request})
        qs = serializer.fields['group'].queryset
        ids = set(qs.values_list('id', flat=True))
        self.assertIn(self.group.id, ids)
        self.assertNotIn(other_group.id, ids)

    def test_teacher_cannot_delete_lessons(self):
        self.client.force_authenticate(self.teacher_user)

        response = self.client.delete(f'/api/academics/lessons/{self.lesson.id}/')
        self.assertEqual(response.status_code, 403)

    def test_student_can_confirm_own_confirmation_only(self):
        participant = self.lesson.participants.get()
        student_confirmation = LessonConfirmation.objects.create(
            participant=participant,
            requested_from=ConfirmationRequester.STUDENT,
        )
        parent_confirmation = LessonConfirmation.objects.create(
            participant=participant,
            requested_from=ConfirmationRequester.PARENT,
        )
        self.client.force_authenticate(self.student_user)

        ok_response = self.client.post(
            f'/api/academics/confirmations/{student_confirmation.id}/confirm/',
            {'comment': 'Done'},
            format='json',
        )
        forbidden_response = self.client.post(
            f'/api/academics/confirmations/{parent_confirmation.id}/confirm/',
            {'comment': 'Wrong role'},
            format='json',
        )

        student_confirmation.refresh_from_db()

        self.assertEqual(ok_response.status_code, 200)
        self.assertEqual(student_confirmation.status, 'confirmed')
        self.assertEqual(forbidden_response.status_code, 404)

    def test_student_parent_teacher_lesson_reschedule_workflow(self):
        requested_starts_at = timezone.now() + timedelta(days=2)
        applied_starts_at = timezone.now() + timedelta(days=3)
        self.client.force_authenticate(self.student_user)

        create_response = self.client.post(
            '/api/academics/reschedule-requests/',
            {
                'lesson': self.lesson.id,
                'requested_starts_at': requested_starts_at.isoformat(),
                'reason': 'Need another time',
            },
            format='json',
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data['status'], LessonRescheduleStatus.PENDING_PARENT)
        self.assertEqual(create_response.data['student'], self.student.id)

        request_id = create_response.data['id']
        self.client.force_authenticate(self.parent_user)
        confirm_response = self.client.post(
            f'/api/academics/reschedule-requests/{request_id}/confirm-parent/',
            {},
            format='json',
        )

        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(confirm_response.data['status'], LessonRescheduleStatus.PARENT_CONFIRMED)
        self.assertEqual(confirm_response.data['parent_confirmed_by'], self.parent_user.id)

        self.client.force_authenticate(self.teacher_user)
        apply_response = self.client.post(
            f'/api/academics/reschedule-requests/{request_id}/apply/',
            {
                'starts_at': applied_starts_at.isoformat(),
                'teacher_comment': 'Moved',
            },
            format='json',
        )

        self.lesson.refresh_from_db()

        self.assertEqual(apply_response.status_code, 200)
        self.assertEqual(apply_response.data['status'], LessonRescheduleStatus.APPLIED)
        self.assertEqual(apply_response.data['applied_by'], self.teacher_user.id)
        self.assertEqual(apply_response.data['teacher_comment'], 'Moved')
        self.assertEqual(self.lesson.starts_at, applied_starts_at)

    def test_reschedule_notifications_route_to_lesson_detail(self):
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            '/api/academics/reschedule-requests/',
            {'lesson': self.lesson.id, 'reason': 'Need another time'},
            format='json',
        )
        request_id = create_response.data['id']

        self.client.force_authenticate(self.parent_user)
        parent_notifications = self.client.get('/api/my/notifications/')

        self.assertEqual(parent_notifications.status_code, 200)
        parent_reschedule = next(item for item in parent_notifications.data if item['id'] == f'reschedule:{request_id}')
        self.assertEqual(parent_reschedule['kind'], 'reschedule')
        self.assertEqual(parent_reschedule['title'], 'Підтвердіть перенесення уроку')
        self.assertEqual(parent_reschedule['message'], f'Учень запросив перенесення уроку #{self.lesson.id}.')
        self.assertEqual(parent_reschedule['url'], f'/my/lessons?lesson={self.lesson.id}')

        self.client.post(
            f'/api/academics/reschedule-requests/{request_id}/confirm-parent/',
            {},
            format='json',
        )

        self.client.force_authenticate(self.teacher_user)
        teacher_notifications = self.client.get('/api/my/notifications/')

        self.assertEqual(teacher_notifications.status_code, 200)
        teacher_reschedule = next(item for item in teacher_notifications.data if item['id'] == f'reschedule:{request_id}')
        self.assertEqual(teacher_reschedule['kind'], 'reschedule')
        self.assertEqual(teacher_reschedule['title'], 'Потрібно перенести урок')
        self.assertEqual(teacher_reschedule['message'], f'Батьки підтвердили перенесення уроку #{self.lesson.id}.')
        self.assertEqual(teacher_reschedule['url'], f'/my/lessons?lesson={self.lesson.id}')

    def test_teacher_cannot_apply_reschedule_before_parent_confirmation(self):
        self.client.force_authenticate(self.student_user)
        create_response = self.client.post(
            '/api/academics/reschedule-requests/',
            {
                'lesson': self.lesson.id,
                'reason': 'Need another time',
            },
            format='json',
        )
        request_id = create_response.data['id']

        self.client.force_authenticate(self.teacher_user)
        response = self.client.post(
            f'/api/academics/reschedule-requests/{request_id}/apply/',
            {'starts_at': (timezone.now() + timedelta(days=2)).isoformat()},
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_reschedule_request_is_only_for_individual_scheduled_lessons(self):
        other_student_user = User.objects.create_user(
            username='reschedule_other_student',
            email='reschedule_other_student@example.com',
            password='pass12345',
            role=UserRole.STUDENT,
        )
        other_student = StudentProfile.objects.create(user=other_student_user, grade='8')
        other_enrollment = StudentEnrollment.objects.create(
            group=self.group,
            student=other_student,
            start_date=timezone.localdate(),
        )
        LessonParticipant.objects.create(lesson=self.lesson, enrollment=other_enrollment)
        self.client.force_authenticate(self.student_user)

        response = self.client.post(
            '/api/academics/reschedule-requests/',
            {'lesson': self.lesson.id, 'reason': 'Need another time'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)

    def test_admin_can_cancel_scheduled_lesson(self):
        admin_user = User.objects.create_user(
            username='admin_api',
            email='admin_api@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        response = self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/cancel/',
            {'reason': 'Teacher sick leave'},
            format='json',
        )

        self.lesson.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.lesson.status, LessonStatus.CANCELLED)
        self.assertEqual(self.lesson.notes, 'Teacher sick leave')

    def test_admin_can_run_finance_workflow_actions(self):
        participant = self.lesson.participants.get()
        participant.attendance_status = AttendanceStatus.PRESENT
        participant.save(update_fields=['attendance_status'])
        self.client.force_authenticate(self.teacher_user)
        self.client.post(
            f'/api/academics/lessons/{self.lesson.id}/complete/',
            {'notes': 'Completed for finance workflow'},
            format='json',
        )

        charge = ParentCharge.objects.get(participant=participant)
        payout = TeacherPayout.objects.get(participant=participant)

        admin_user = User.objects.create_user(
            username='finance_admin',
            email='finance_admin@example.com',
            password='pass12345',
            role=UserRole.ADMIN,
            is_staff=True,
        )
        self.client.force_authenticate(admin_user)

        issue_response = self.client.post(
            f'/api/finance/parent-charges/{charge.id}/issue/',
            {'due_date': '2026-03-31'},
            format='json',
        )
        charge_paid_response = self.client.post(
            f'/api/finance/parent-charges/{charge.id}/mark-paid/',
            {},
            format='json',
        )
        approve_response = self.client.post(
            f'/api/finance/teacher-payouts/{payout.id}/approve/',
            {},
            format='json',
        )
        payout_paid_response = self.client.post(
            f'/api/finance/teacher-payouts/{payout.id}/mark-paid/',
            {},
            format='json',
        )

        charge.refresh_from_db()
        payout.refresh_from_db()

        self.assertEqual(issue_response.status_code, 200)
        self.assertEqual(charge_paid_response.status_code, 200)
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(payout_paid_response.status_code, 200)
        self.assertEqual(charge.status, ChargeStatus.PAID)
        self.assertEqual(str(charge.due_date), '2026-03-31')
        self.assertIsNotNone(charge.paid_at)
        self.assertEqual(payout.status, PayoutStatus.PAID)
        self.assertIsNotNone(payout.approved_at)
        self.assertIsNotNone(payout.paid_at)

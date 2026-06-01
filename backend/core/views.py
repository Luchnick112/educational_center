from decimal import Decimal

from django.db.models import Q, Sum
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import AttendanceStatus, Lesson, LessonConfirmation, LessonRescheduleRequest, LessonRescheduleStatus
from academics.serializers import LessonConfirmationSerializer, LessonSerializer
from finance.models import ChargeStatus, ParentCharge, PayoutStatus, StudentPayment, TeacherPayment, TeacherPayout
from finance.serializers import ParentChargeSerializer, StudentPaymentSerializer, TeacherPaymentSerializer, TeacherPayoutSerializer
from users.models import StudentProfile, UserRole
from users.serializers import ParentProfileSerializer, StudentProfileSerializer
from .serializers import EmptyObjectSerializer, MeSerializer, MyPaymentsSerializer, NotificationSerializer


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        def _url(name: str) -> str:
            # Return relative URLs so the frontend can resolve them against its configured API base.
            # Absolute URLs make local dev annoying (localhost vs 127.0.0.1) and are not needed here.
            return reverse(name)

        def _find_my_resolvers():
            resolver = get_resolver()
            stack = [resolver]
            while stack:
                current = stack.pop()
                for pattern in getattr(current, "url_patterns", []):
                    if isinstance(pattern, URLResolver):
                        if pattern.namespace == "my":
                            yield pattern
                        stack.append(pattern)

        my_links = []
        # Discoverability: expose all "my:" endpoints from the URLconf.
        for my_resolver in _find_my_resolvers():
            for pattern in getattr(my_resolver, "url_patterns", []):
                if not isinstance(pattern, URLPattern):
                    continue
                name = getattr(pattern, "name", None)
                if not name or getattr(pattern, "pattern", None) is None or getattr(pattern.pattern, "converters", None):
                    continue
                my_links.append({"key": str(name).replace("-", "_"), "url": _url(f"my:{name}")})
        my_links.sort(key=lambda item: item["key"])

        return Response(
            {
                'id': request.user.id,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'telegram_username': request.user.telegram_username or '',
                'email': request.user.email,
                'role': request.user.role,
                'is_staff': request.user.is_staff,
                'my': my_links,
            }
        )


class MyLessonsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=LessonSerializer(many=True))
    def get(self, request):
        user = request.user
        queryset = Lesson.objects.none()

        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            queryset = Lesson.objects.filter(participants__student=user.student_profile).distinct()
        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            queryset = Lesson.objects.filter(
                participants__student__parent_links__parent=user.parent_profile,
            ).distinct()
        elif user.role == UserRole.TEACHER and not user.is_staff and hasattr(user, 'teacher_profile'):
            queryset = Lesson.objects.filter(group__teacher=user.teacher_profile)
        elif user.is_staff or user.role == UserRole.ADMIN:
            queryset = Lesson.objects.all()

        date_from = parse_date(request.query_params.get('date_from', ''))
        date_to = parse_date(request.query_params.get('date_to', ''))
        has_date_filter = date_from is not None or date_to is not None

        if date_from is not None:
            queryset = queryset.filter(starts_at__date__gte=date_from)
        if date_to is not None:
            queryset = queryset.filter(starts_at__date__lte=date_to)

        queryset = queryset.annotate(
            payroll_amount_total=Sum(
                'participants__payroll_amount',
                filter=Q(participants__attendance_status=AttendanceStatus.PRESENT),
            ),
            billed_amount_total=Sum('participants__billed_amount'),
        ).order_by('starts_at')
        if not has_date_filter:
            queryset = queryset[:20]

        serializer = LessonSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class MyChildrenView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=StudentProfileSerializer(many=True))
    def get(self, request):
        user = request.user
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            students = [link.student for link in user.parent_profile.student_links.select_related('student', 'student__user')]
            serializer = StudentProfileSerializer(students, many=True)
            return Response(serializer.data)

        if user.is_staff or user.role == UserRole.ADMIN:
            serializer = StudentProfileSerializer(StudentProfile.objects.select_related('user').all(), many=True)
            return Response(serializer.data)

        return Response([])


class MyPaymentsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=MyPaymentsSerializer)
    def get(self, request):
        user = request.user
        date_from = parse_date(request.query_params.get('date_from', ''))
        date_to = parse_date(request.query_params.get('date_to', ''))
        student_id = request.query_params.get('student')
        teacher_id = request.query_params.get('teacher')

        def apply_lesson_date_filters(queryset):
            if date_from is not None:
                queryset = queryset.filter(participant__lesson__starts_at__date__gte=date_from)
            if date_to is not None:
                queryset = queryset.filter(participant__lesson__starts_at__date__lte=date_to)
            return queryset

        def apply_payment_date_filters(queryset):
            if date_from is not None:
                queryset = queryset.filter(paid_at__gte=date_from)
            if date_to is not None:
                queryset = queryset.filter(paid_at__lte=date_to)
            return queryset

        def parse_id(value):
            try:
                return int(value) if value not in (None, '') else None
            except (TypeError, ValueError):
                return None

        def money(value: Decimal) -> str:
            return f'{value:.2f}'

        def profile_label(profile) -> str:
            profile_user = profile.user
            full_name = profile_user.get_full_name().strip()
            return full_name or profile_user.telegram_username or profile_user.email or f'#{profile.id}'

        def recompute_paid_debt_counts(rows, paid_amount: Decimal, sort_key):
            paid_remaining = paid_amount
            paid_count = 0
            debt_count = 0
            for row in sorted(rows, key=sort_key):
                amount = row.amount
                if paid_remaining >= amount:
                    paid_count += 1
                    paid_remaining -= amount
                else:
                    debt_count += 1
                    paid_remaining = Decimal('0.00')
            return paid_count, debt_count

        if user.is_staff or user.role == UserRole.ADMIN:
            charges = apply_lesson_date_filters(
                ParentCharge.objects.select_related(
                    'parent__user',
                    'student__user',
                    'participant__lesson',
                )
            ).order_by('-issued_at')
            payouts = apply_lesson_date_filters(
                TeacherPayout.objects.select_related(
                    'teacher__user',
                    'participant__lesson',
                    'participant__student__user',
                )
            ).order_by('-id')
            student_payments = apply_payment_date_filters(
                StudentPayment.objects.select_related('student__user', 'created_by')
            ).order_by('-paid_at', '-id')
            teacher_payments = apply_payment_date_filters(
                TeacherPayment.objects.select_related('teacher__user', 'created_by')
            ).order_by('-paid_at', '-id')
            selected_student_id = parse_id(student_id)
            selected_teacher_id = parse_id(teacher_id)
            if selected_student_id is not None:
                charges = charges.filter(student_id=selected_student_id)
                student_payments = student_payments.filter(student_id=selected_student_id)
            if selected_teacher_id is not None:
                payouts = payouts.filter(teacher_id=selected_teacher_id)
                teacher_payments = teacher_payments.filter(teacher_id=selected_teacher_id)

            student_summaries = {}
            charges_by_student = {}
            for charge in charges:
                item = student_summaries.setdefault(
                    charge.student_id,
                    {
                        'student': charge.student_id,
                        'student_name': profile_label(charge.student),
                        'charged_amount': Decimal('0.00'),
                        'paid_amount': Decimal('0.00'),
                        'debt_amount': Decimal('0.00'),
                        'charge_count': 0,
                        'paid_count': 0,
                        'debt_count': 0,
                    },
                )
                if charge.status == ChargeStatus.CANCELLED:
                    continue
                charges_by_student.setdefault(charge.student_id, []).append(charge)
                item['charged_amount'] += charge.amount
                item['charge_count'] += 1

            for payment in student_payments:
                item = student_summaries.setdefault(
                    payment.student_id,
                    {
                        'student': payment.student_id,
                        'student_name': profile_label(payment.student),
                        'charged_amount': Decimal('0.00'),
                        'paid_amount': Decimal('0.00'),
                        'debt_amount': Decimal('0.00'),
                        'charge_count': 0,
                        'paid_count': 0,
                        'debt_count': 0,
                    },
                )
                item['paid_amount'] += payment.amount

            for item in student_summaries.values():
                item['debt_amount'] = max(item['charged_amount'] - item['paid_amount'], Decimal('0.00'))
                item['paid_count'], item['debt_count'] = recompute_paid_debt_counts(
                    charges_by_student.get(item['student'], []),
                    item['paid_amount'],
                    lambda charge: (charge.participant.lesson.starts_at, charge.id),
                )

            teacher_summaries = {}
            payouts_by_teacher = {}
            for payout in payouts:
                item = teacher_summaries.setdefault(
                    payout.teacher_id,
                    {
                        'teacher': payout.teacher_id,
                        'teacher_name': profile_label(payout.teacher),
                        'accrued_amount': Decimal('0.00'),
                        'paid_amount': Decimal('0.00'),
                        'debt_amount': Decimal('0.00'),
                        'payout_count': 0,
                        'paid_count': 0,
                        'debt_count': 0,
                    },
                )
                if payout.status == PayoutStatus.CANCELLED:
                    continue
                payouts_by_teacher.setdefault(payout.teacher_id, []).append(payout)
                item['accrued_amount'] += payout.amount
                item['payout_count'] += 1

            for payment in teacher_payments:
                item = teacher_summaries.setdefault(
                    payment.teacher_id,
                    {
                        'teacher': payment.teacher_id,
                        'teacher_name': profile_label(payment.teacher),
                        'accrued_amount': Decimal('0.00'),
                        'paid_amount': Decimal('0.00'),
                        'debt_amount': Decimal('0.00'),
                        'payout_count': 0,
                        'paid_count': 0,
                        'debt_count': 0,
                    },
                )
                item['paid_amount'] += payment.amount

            for item in teacher_summaries.values():
                item['debt_amount'] = max(item['accrued_amount'] - item['paid_amount'], Decimal('0.00'))
                item['paid_count'], item['debt_count'] = recompute_paid_debt_counts(
                    payouts_by_teacher.get(item['teacher'], []),
                    item['paid_amount'],
                    lambda payout: (payout.participant.lesson.starts_at, payout.id),
                )

            def serialize_summary_rows(rows, amount_keys):
                serialized = []
                for row in rows:
                    item = dict(row)
                    for key in amount_keys:
                        item[key] = money(item[key])
                    serialized.append(item)
                return serialized

            student_rows = sorted(
                student_summaries.values(),
                key=lambda item: (item['debt_amount'], item['student_name']),
                reverse=True,
            )
            teacher_rows = sorted(
                teacher_summaries.values(),
                key=lambda item: (item['debt_amount'], item['teacher_name']),
                reverse=True,
            )

            return Response(
                {
                    'period': {
                        'date_from': date_from.isoformat() if date_from else None,
                        'date_to': date_to.isoformat() if date_to else None,
                    },
                    'charges': ParentChargeSerializer(charges, many=True).data,
                    'payouts': TeacherPayoutSerializer(payouts, many=True).data,
                    'student_payments': StudentPaymentSerializer(student_payments, many=True).data,
                    'teacher_payments': TeacherPaymentSerializer(teacher_payments, many=True).data,
                    'student_summaries': serialize_summary_rows(
                        student_rows,
                        ('charged_amount', 'paid_amount', 'debt_amount'),
                    ),
                    'teacher_summaries': serialize_summary_rows(
                        teacher_rows,
                        ('accrued_amount', 'paid_amount', 'debt_amount'),
                    ),
                }
            )

        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            charges = apply_lesson_date_filters(
                ParentCharge.objects.select_related(
                    'parent__user',
                    'student__user',
                    'participant__lesson',
                ).filter(parent=user.parent_profile)
            ).order_by('-issued_at')
            student_payments = apply_payment_date_filters(
                StudentPayment.objects.select_related('student__user', 'created_by').filter(
                    student__parent_links__parent=user.parent_profile,
                )
            ).order_by('-paid_at', '-id').distinct()
            return Response(
                {
                    'charges': ParentChargeSerializer(charges, many=True).data,
                    'payouts': [],
                    'student_payments': StudentPaymentSerializer(student_payments, many=True).data,
                    'teacher_payments': [],
                }
            )
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            payouts = apply_lesson_date_filters(
                TeacherPayout.objects.select_related(
                    'teacher__user',
                    'participant__lesson',
                    'participant__student__user',
                ).filter(teacher=user.teacher_profile)
            ).order_by('-id')
            teacher_payments = apply_payment_date_filters(
                TeacherPayment.objects.select_related('teacher__user', 'created_by').filter(teacher=user.teacher_profile)
            ).order_by('-paid_at', '-id')
            return Response(
                {
                    'charges': [],
                    'payouts': TeacherPayoutSerializer(payouts, many=True).data,
                    'student_payments': [],
                    'teacher_payments': TeacherPaymentSerializer(teacher_payments, many=True).data,
                }
            )
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            charges = apply_lesson_date_filters(
                ParentCharge.objects.select_related(
                    'parent__user',
                    'student__user',
                    'participant__lesson',
                ).filter(student=user.student_profile)
            ).order_by('-issued_at')
            student_payments = apply_payment_date_filters(
                StudentPayment.objects.select_related('student__user', 'created_by').filter(student=user.student_profile)
            ).order_by('-paid_at', '-id')
            return Response(
                {
                    'charges': ParentChargeSerializer(charges, many=True).data,
                    'payouts': [],
                    'student_payments': StudentPaymentSerializer(student_payments, many=True).data,
                    'teacher_payments': [],
                }
            )
        return Response({'charges': [], 'payouts': [], 'student_payments': [], 'teacher_payments': []})


class MyConfirmationsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=LessonConfirmationSerializer(many=True))
    def get(self, request):
        user = request.user
        queryset = LessonConfirmation.objects.none()

        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            queryset = LessonConfirmation.objects.filter(
                participant__student=user.student_profile,
                requested_from='student',
            )
        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            queryset = LessonConfirmation.objects.filter(
                participant__student__parent_links__parent=user.parent_profile,
                requested_from='parent',
            ).distinct()
        elif user.role == UserRole.TEACHER and not user.is_staff and hasattr(user, 'teacher_profile'):
            queryset = LessonConfirmation.objects.filter(
                participant__lesson__group__teacher=user.teacher_profile,
                requested_from='teacher',
            )
        elif user.is_staff or user.role == UserRole.ADMIN:
            queryset = LessonConfirmation.objects.all()

        serializer = LessonConfirmationSerializer(queryset.order_by('-id')[:50], many=True)
        return Response(serializer.data)


class MyNotificationsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=NotificationSerializer(many=True))
    def get(self, request):
        user = request.user
        notifications = []

        def add(kind, item_id, title, message, url, created_at=None):
            notifications.append(
                {
                    'id': f'{kind}:{item_id}',
                    'kind': kind,
                    'title': title,
                    'message': message,
                    'url': url,
                    'created_at': created_at,
                }
            )

        def uncovered_student_charges(charges, payments):
            paid_by_student = {}
            for payment in payments:
                paid_by_student[payment.student_id] = (
                    paid_by_student.get(payment.student_id, Decimal('0.00')) + payment.amount
                )

            charges_by_student = {}
            for charge in charges:
                if charge.status == ChargeStatus.CANCELLED:
                    continue
                charges_by_student.setdefault(charge.student_id, []).append(charge)

            uncovered = []
            for student_id, student_charges in charges_by_student.items():
                paid_remaining = paid_by_student.get(student_id, Decimal('0.00'))
                for charge in sorted(
                    student_charges,
                    key=lambda item: (item.participant.lesson.starts_at, item.id),
                ):
                    if paid_remaining >= charge.amount:
                        paid_remaining -= charge.amount
                    elif charge.status == ChargeStatus.PAID:
                        continue
                    else:
                        uncovered.append(charge)
                        paid_remaining = Decimal('0.00')
            return uncovered

        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            charges = ParentCharge.objects.select_related('participant__lesson').filter(student=user.student_profile)
            payments = StudentPayment.objects.filter(student=user.student_profile)
            for charge in uncovered_student_charges(charges, payments):
                add(
                    'payment',
                    charge.id,
                    'Є неоплачений платіж',
                    f'Платіж на суму {charge.amount} очікує оплати.',
                    '/my/payments',
                    charge.issued_at,
                )

        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            reschedules = LessonRescheduleRequest.objects.filter(
                student__parent_links__parent=user.parent_profile,
                status=LessonRescheduleStatus.PENDING_PARENT,
            ).select_related('lesson').distinct()
            for reschedule in reschedules:
                add(
                    'reschedule',
                    reschedule.id,
                    'Підтвердіть перенесення уроку',
                    f'Учень запросив перенесення уроку #{reschedule.lesson_id}.',
                    f'/my/lessons?lesson={reschedule.lesson_id}',
                    reschedule.created_at,
                )

            charges = ParentCharge.objects.select_related('participant__lesson').filter(parent=user.parent_profile)
            payments = StudentPayment.objects.filter(
                student__parent_links__parent=user.parent_profile,
            ).distinct()
            for charge in uncovered_student_charges(charges, payments):
                add(
                    'payment',
                    charge.id,
                    'Є неоплачений платіж',
                    f'Платіж на суму {charge.amount} очікує оплати.',
                    '/my/payments',
                    charge.issued_at,
                )

        elif user.role == UserRole.TEACHER and not user.is_staff and hasattr(user, 'teacher_profile'):
            reschedules = LessonRescheduleRequest.objects.filter(
                lesson__group__teacher=user.teacher_profile,
                status=LessonRescheduleStatus.PARENT_CONFIRMED,
            ).select_related('lesson')
            for reschedule in reschedules:
                add(
                    'reschedule',
                    reschedule.id,
                    'Потрібно перенести урок',
                    f'Батьки підтвердили перенесення уроку #{reschedule.lesson_id}.',
                    f'/my/lessons?lesson={reschedule.lesson_id}',
                    reschedule.parent_confirmed_at or reschedule.created_at,
                )

            payouts = TeacherPayout.objects.filter(
                teacher=user.teacher_profile,
                status=PayoutStatus.APPROVED,
            )
            for payout in payouts:
                add(
                    'payout',
                    payout.id,
                    'Є виплата в обробці',
                    f'Виплата на суму {payout.amount} має статус {payout.status}.',
                    '/my/payments',
                    payout.approved_at,
                )

            teacher_payments = TeacherPayment.objects.filter(
                teacher=user.teacher_profile,
            ).select_related('teacher').order_by('-created_at')[:10]
            for payment in teacher_payments:
                add(
                    'teacher_payment',
                    payment.id,
                    'Надійшла виплата',
                    f'Вам внесено виплату {payment.amount} від {payment.paid_at}.',
                    '/my/payments',
                    payment.created_at,
                )

        elif user.is_staff or user.role == UserRole.ADMIN:
            reschedules = LessonRescheduleRequest.objects.filter(
                status__in=(LessonRescheduleStatus.PENDING_PARENT, LessonRescheduleStatus.PARENT_CONFIRMED),
            ).select_related('lesson')
            for reschedule in reschedules:
                add(
                    'reschedule',
                    reschedule.id,
                    'Активний запит на перенесення',
                    f'Урок #{reschedule.lesson_id}: {reschedule.status}.',
                    f'/my/lessons?lesson={reschedule.lesson_id}',
                    reschedule.updated_at,
                )

        notifications.sort(key=lambda item: str(item.get('created_at') or ''), reverse=True)
        serializer = NotificationSerializer(notifications[:20], many=True)
        return Response(serializer.data)


class MyChildrenSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        responses={
            200: ParentProfileSerializer,
            204: EmptyObjectSerializer,
        }
    )
    def get(self, request):
        user = request.user
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            serializer = ParentProfileSerializer(user.parent_profile)
            return Response(serializer.data)
        return Response({})

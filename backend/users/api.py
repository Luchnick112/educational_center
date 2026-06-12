import secrets
from datetime import timedelta

from drf_spectacular.utils import extend_schema
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from academics.models import Lesson, LessonParticipant, StudentEnrollment
from core.serializers import DashboardSerializer
from finance.models import ParentCharge, TeacherPayout

from .models import (
    ParentProfile,
    StudentParentRelation,
    StudentProfile,
    TeacherProfile,
    TelegramLinkToken,
    User,
    UserRole,
)
from .permissions import StaffOrTeacherWritePermission, StaffWritePermission
from .serializers import (
    ParentProfileSerializer,
    TelegramUsernameTokenObtainPairSerializer,
    EmailTokenRefreshSerializer,
    RegisterSerializer,
    StudentProfileSerializer,
    StudentParentRelationSerializer,
    TeacherProfileSerializer,
    TelegramLinkTokenResponseSerializer,
    TelegramWebhookSerializer,
    UserSerializer,
)
from .services.telegram_linking import link_user_by_start_token


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = (StaffWritePermission,)
    # Prevent the catch-all "/api/users/<pk>/" route from swallowing other prefixes
    # like "/api/users/student-parent-relations/".
    lookup_value_regex = r'\d+'

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()

        if user.is_staff or user.role == UserRole.ADMIN:
            return super().get_queryset()
        return User.objects.filter(pk=user.pk)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @extend_schema(request=UserSerializer, responses=UserSerializer)
    @decorators.action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return response.Response(serializer.data)

        serializer = self.get_serializer(request.user)
        return response.Response(serializer.data)

    @extend_schema(responses=DashboardSerializer)
    @decorators.action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        user = request.user
        data = {
            'user': self.get_serializer(user).data,
            'role': user.role,
            'stats': {},
        }

        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            student = user.student_profile
            data['stats'] = {
                'Активні зарахування': StudentEnrollment.objects.filter(student=student, status='active').count(),
                'Заплановані уроки': LessonParticipant.objects.filter(
                    student=student,
                    lesson__status='scheduled',
                ).count(),
            }
        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            parent = user.parent_profile
            data['stats'] = {
                'Діти': parent.student_links.count(),
                'Відкриті нарахування': ParentCharge.objects.filter(parent=parent).exclude(status='paid').count(),
            }
        elif user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            data['stats'] = {
                'Групи': teacher.groups.count(),
                'Заплановані уроки': Lesson.objects.filter(group__teacher=teacher, status='scheduled').count(),
                'Очікують виплати': TeacherPayout.objects.filter(teacher=teacher).exclude(status='paid').count(),
            }
        else:
            data['stats'] = {
                'Користувачі': User.objects.count(),
                'Студенти': StudentProfile.objects.filter(user__is_active=True).count(),
                'Вчителі': TeacherProfile.objects.filter(user__is_active=True).count(),
                'Групи': StudentEnrollment.objects.values('group').distinct().count(),
                'Заплановані уроки': Lesson.objects.filter(status='scheduled').count(),
                'Відкриті нарахування': ParentCharge.objects.exclude(status='paid').count(),
            }

        return response.Response(data)


class DeactivateProfileUserOnDestroyMixin:
    def perform_destroy(self, instance):
        user = instance.user
        user.is_active = False
        user.save(update_fields=['is_active'])


class StudentProfileViewSet(DeactivateProfileUserOnDestroyMixin, viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related('user').all()
    serializer_class = StudentProfileSerializer
    permission_classes = (StaffOrTeacherWritePermission,)

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(user__is_active=True)
        if user.is_staff or user.role == UserRole.ADMIN:
            return queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return queryset
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return queryset.filter(pk=user.student_profile.pk)
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return queryset.filter(parent_links__parent=user.parent_profile).distinct()
        return queryset.none()


class ParentProfileViewSet(DeactivateProfileUserOnDestroyMixin, viewsets.ModelViewSet):
    queryset = ParentProfile.objects.select_related('user').prefetch_related('student_links__student__user').all()
    serializer_class = ParentProfileSerializer
    permission_classes = (StaffWritePermission,)

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(user__is_active=True)
        if user.is_staff or user.role == UserRole.ADMIN:
            return queryset
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return queryset.filter(pk=user.parent_profile.pk)
        return queryset.none()


class StudentParentRelationViewSet(viewsets.ModelViewSet):
    queryset = StudentParentRelation.objects.select_related('parent__user', 'student__user').all()
    serializer_class = StudentParentRelationSerializer
    permission_classes = (StaffWritePermission,)

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return StudentParentRelation.objects.none()

        if user.is_staff or user.role == UserRole.ADMIN:
            return super().get_queryset()

        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(parent=user.parent_profile)

        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)

        return StudentParentRelation.objects.none()


class TeacherProfileViewSet(DeactivateProfileUserOnDestroyMixin, viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.select_related('user').all()
    serializer_class = TeacherProfileSerializer
    permission_classes = (StaffWritePermission,)

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(user__is_active=True)
        if user.is_staff or user.role == UserRole.ADMIN:
            return queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return queryset.filter(pk=user.teacher_profile.pk)
        return queryset.none()


class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(exclude=True)
    def get(self, request):
        return render(request, 'users/register.html', {'roles': UserRole.choices})

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class TokenPageView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = TelegramUsernameTokenObtainPairSerializer

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        return render(
            request,
            'users/auth_form.html',
            {
                'page_title': 'Get access tokens',
                'page_lead': 'Enter Telegram username and password to receive JWT access and refresh tokens.',
                'button_label': 'Get tokens',
                'endpoint': '/api/users/token/',
                'fields': (
                    {'name': 'login', 'label': 'Telegram, email or phone', 'type': 'text', 'required': True},
                    {'name': 'password', 'label': 'Password', 'type': 'password', 'required': True},
                ),
            },
        )


class TokenRefreshPageView(TokenRefreshView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmailTokenRefreshSerializer

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        return render(
            request,
            'users/auth_form.html',
            {
                'page_title': 'Refresh access token',
                'page_lead': 'Paste a refresh token to receive a new access token without logging in again.',
                'button_label': 'Refresh token',
                'endpoint': '/api/users/token/refresh/',
                'fields': (
                    {'name': 'refresh', 'label': 'Refresh token', 'type': 'text', 'required': True},
                ),
            },
        )


class TelegramLinkTokenView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def _generate_token(self) -> str:
        # Telegram deep-link payload is limited; keep it short but unguessable.
        # token_urlsafe(24) ~ 32 chars.
        for _ in range(10):
            candidate = secrets.token_urlsafe(24)
            if not TelegramLinkToken.objects.filter(token=candidate).exists():
                return candidate
        # Extremely unlikely; fallback to a longer token.
        return secrets.token_urlsafe(48)

    @extend_schema(request=None, responses={200: TelegramLinkTokenResponseSerializer})
    def post(self, request):
        token = self._generate_token()
        ttl_seconds = max(60, int(getattr(settings, 'TELEGRAM_LINK_TOKEN_TTL_SECONDS', 600)))
        expires_at = timezone.now() + timedelta(seconds=ttl_seconds)

        TelegramLinkToken.objects.create(
            user=request.user,
            token=token,
            expires_at=expires_at,
        )

        bot_username = (getattr(settings, 'TELEGRAM_BOT_USERNAME', '') or '').strip().lstrip('@')
        deep_link_url = ''
        if bot_username:
            deep_link_url = f'https://t.me/{bot_username}?start={token}'

        data = {
            'token': token,
            'expires_at': expires_at,
            'deep_link_url': deep_link_url,
        }
        return response.Response(data, status=status.HTTP_200_OK)


class TelegramWebhookView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(request=TelegramWebhookSerializer, responses={200: dict})
    def post(self, request):
        payload = request.data or {}
        serializer = TelegramWebhookSerializer(data=payload)
        serializer.is_valid(raise_exception=False)

        message = payload.get('message') or payload.get('edited_message') or {}
        text = (message.get('text') or '').strip()

        if not text.startswith('/start'):
            return response.Response({'ok': True})

        parts = text.split(maxsplit=1)
        if len(parts) != 2:
            return response.Response({'ok': True})

        token_value = parts[1].strip()
        if not token_value:
            return response.Response({'ok': True})

        chat = message.get('chat') or {}
        from_user = message.get('from') or {}
        chat_id = chat.get('id')
        telegram_user_id = from_user.get('id')
        telegram_username = (from_user.get('username') or '').strip()

        if chat_id is None or telegram_user_id is None:
            return response.Response({'ok': True})

        link_user_by_start_token(
            token=token_value,
            chat_id=int(chat_id),
            telegram_user_id=int(telegram_user_id),
            telegram_username=telegram_username,
        )

        return response.Response({'ok': True})

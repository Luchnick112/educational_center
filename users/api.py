from drf_spectacular.utils import extend_schema
from django.shortcuts import render
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from academics.models import Lesson, LessonConfirmation, LessonParticipant, StudentEnrollment
from core.serializers import DashboardSerializer
from finance.models import ParentCharge, TeacherPayout

from .models import ParentProfile, StudentProfile, TeacherProfile, User, UserRole
from .permissions import StaffWritePermission
from .serializers import (
    ParentProfileSerializer,
    EmailTokenObtainPairSerializer,
    EmailTokenRefreshSerializer,
    RegisterSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = (StaffWritePermission,)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return super().get_queryset()
        return User.objects.filter(pk=user.pk)

    @extend_schema(responses=UserSerializer)
    @decorators.action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
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
                'active_enrollments': StudentEnrollment.objects.filter(student=student, status='active').count(),
                'upcoming_lessons': LessonParticipant.objects.filter(
                    student=student,
                    lesson__status='scheduled',
                ).count(),
                'pending_confirmations': LessonConfirmation.objects.filter(
                    participant__student=student,
                    requested_from=UserRole.STUDENT,
                    status='pending',
                ).count(),
            }
        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            parent = user.parent_profile
            data['stats'] = {
                'children': parent.student_links.count(),
                'open_charges': ParentCharge.objects.filter(parent=parent).exclude(status='paid').count(),
                'pending_confirmations': LessonConfirmation.objects.filter(
                    participant__student__parent_links__parent=parent,
                    requested_from=UserRole.PARENT,
                    status='pending',
                ).distinct().count(),
            }
        elif user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            data['stats'] = {
                'groups': teacher.groups.count(),
                'scheduled_lessons': Lesson.objects.filter(group__teacher=teacher, status='scheduled').count(),
                'pending_payouts': TeacherPayout.objects.filter(teacher=teacher).exclude(status='paid').count(),
            }
        else:
            data['stats'] = {
                'users': User.objects.count(),
                'groups': StudentEnrollment.objects.values('group').distinct().count(),
                'scheduled_lessons': Lesson.objects.filter(status='scheduled').count(),
                'open_charges': ParentCharge.objects.exclude(status='paid').count(),
            }

        return response.Response(data)


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.select_related('user').all()
    serializer_class = StudentProfileSerializer
    permission_classes = (StaffWritePermission,)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return super().get_queryset()
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(pk=user.student_profile.pk)
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(parent_links__parent=user.parent_profile).distinct()
        return self.queryset.none()


class ParentProfileViewSet(viewsets.ModelViewSet):
    queryset = ParentProfile.objects.select_related('user').all()
    serializer_class = ParentProfileSerializer
    permission_classes = (StaffWritePermission,)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return super().get_queryset()
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(pk=user.parent_profile.pk)
        return self.queryset.none()


class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.select_related('user').all()
    serializer_class = TeacherProfileSerializer
    permission_classes = (StaffWritePermission,)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return super().get_queryset()
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(pk=user.teacher_profile.pk)
        return self.queryset.none()


class RegisterView(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(exclude=True)
    def get(self, request):
        return render(request, 'users/register.html', {'roles': UserRole.choices})

    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return response.Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class TokenPageView(TokenObtainPairView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmailTokenObtainPairSerializer

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        return render(
            request,
            'users/auth_form.html',
            {
                'page_title': 'Get access tokens',
                'page_lead': 'Enter email and password to receive JWT access and refresh tokens.',
                'button_label': 'Get tokens',
                'endpoint': '/api/users/token/',
                'fields': (
                    {'name': 'email', 'label': 'Email', 'type': 'email', 'required': True},
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

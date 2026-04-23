from django.db.models import Prefetch
from rest_framework import decorators, exceptions, permissions, response, viewsets

from users.models import UserRole
from users.permissions import IsAdminOrRelatedAcademicObject, StaffWritePermission

from .models import (
    Lesson,
    LessonConfirmation,
    LessonParticipant,
    LessonStatus,
    StudentEnrollment,
    StudyGroup,
    Subject,
)
from .serializers import (
    AttendanceMarkSerializer,
    LessonCancelSerializer,
    LessonCompletionSerializer,
    LessonConfirmSerializer,
    LessonConfirmationSerializer,
    LessonSerializer,
    StudentEnrollmentSerializer,
    StudyGroupSerializer,
    SubjectSerializer,
)
from .services import cancel_lesson, complete_lesson, confirm_lesson, mark_lesson_attendance


class StaffOrTeacherScheduleWritePermission(permissions.BasePermission):
    """
    Allow teachers to create/update their own lessons (schedule) while keeping
    admin/staff full write access and everyone else read-only.
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return bool(user and user.is_authenticated)

        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.role == UserRole.ADMIN:
            return True

        # Teachers can manage their schedule via LessonViewSet only.
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return getattr(view, 'action', None) in {'create', 'update', 'partial_update'}

        return False


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer
    permission_classes = (StaffWritePermission,)


class StudyGroupViewSet(viewsets.ModelViewSet):
    queryset = StudyGroup.objects.select_related('subject', 'teacher', 'teacher__user').all()
    serializer_class = StudyGroupSerializer
    permission_classes = (StaffWritePermission, IsAdminOrRelatedAcademicObject)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(teacher=user.teacher_profile)
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(enrollments__student=user.student_profile).distinct()
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(enrollments__student__parent_links__parent=user.parent_profile).distinct()
        return self.queryset.none()


class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = StudentEnrollment.objects.select_related('group', 'student', 'student__user').all()
    serializer_class = StudentEnrollmentSerializer
    permission_classes = (StaffWritePermission, IsAdminOrRelatedAcademicObject)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(group__teacher=user.teacher_profile)
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(student__parent_links__parent=user.parent_profile).distinct()
        return self.queryset.none()


class LessonViewSet(viewsets.ModelViewSet):
    queryset = (
        Lesson.objects.select_related(
            'group',
            'group__subject',
            'group__teacher',
            'group__teacher__user',
        )
        .prefetch_related(
            Prefetch(
                'participants',
                queryset=LessonParticipant.objects.select_related('student__user', 'enrollment'),
            ),
        )
        .all()
    )
    serializer_class = LessonSerializer
    permission_classes = (StaffOrTeacherScheduleWritePermission, IsAdminOrRelatedAcademicObject)

    def get_permissions(self):
        if getattr(self, 'action', None) in {'mark_attendance', 'complete', 'cancel'}:
            return [permissions.IsAuthenticated(), IsAdminOrRelatedAcademicObject()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(group__teacher=user.teacher_profile)
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(participants__student=user.student_profile).distinct()
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(
                participants__student__parent_links__parent=user.parent_profile,
            ).distinct()
        return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        group = serializer.validated_data['group']

        if user.is_staff or user.role == UserRole.ADMIN:
            serializer.save()
            return

        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            if group.teacher_id != user.teacher_profile.id:
                raise exceptions.PermissionDenied('You can only create lessons for your own groups.')
            status = serializer.validated_data.get('status', LessonStatus.SCHEDULED)
            if status != LessonStatus.SCHEDULED:
                raise exceptions.ValidationError({'status': 'Only scheduled lessons can be created.'})
            serializer.save(status=LessonStatus.SCHEDULED)
            return

        raise exceptions.PermissionDenied('You cannot create lessons.')

    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if not (user.is_staff or user.role == UserRole.ADMIN):
            if instance.status != LessonStatus.SCHEDULED:
                raise exceptions.ValidationError({'detail': 'Only scheduled lessons can be updated.'})
            if 'status' in serializer.validated_data and serializer.validated_data['status'] != instance.status:
                raise exceptions.ValidationError({'status': 'Status cannot be changed here.'})
            if 'group' in serializer.validated_data and serializer.validated_data['group'].id != instance.group_id:
                raise exceptions.ValidationError({'group': 'Lesson group cannot be changed.'})

        serializer.save()

    @decorators.action(detail=True, methods=['post'], url_path='mark-attendance')
    def mark_attendance(self, request, pk=None):
        lesson = self.get_object()
        serializer = AttendanceMarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = mark_lesson_attendance(
            user=request.user,
            lesson=lesson,
            participant_id=serializer.validated_data['participant_id'],
            attendance_status=serializer.validated_data['attendance_status'],
        )
        return response.Response(result)

    @decorators.action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        lesson = self.get_object()
        serializer = LessonCompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = complete_lesson(
            user=request.user,
            lesson=lesson,
            notes=serializer.validated_data.get('notes', ''),
        )
        return response.Response(self.get_serializer(lesson).data)

    @decorators.action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        lesson = self.get_object()
        serializer = LessonCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = cancel_lesson(user=request.user, lesson=lesson, reason=serializer.validated_data['reason'])
        return response.Response(self.get_serializer(lesson).data)


class LessonConfirmationViewSet(viewsets.ModelViewSet):
    queryset = LessonConfirmation.objects.select_related('participant', 'confirmer').all()
    serializer_class = LessonConfirmationSerializer
    permission_classes = (StaffWritePermission, IsAdminOrRelatedAcademicObject)

    def get_permissions(self):
        if getattr(self, 'action', None) == 'confirm':
            return [permissions.IsAuthenticated(), IsAdminOrRelatedAcademicObject()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(participant__lesson__group__teacher=user.teacher_profile)
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(
                participant__student=user.student_profile,
                requested_from='student',
            )
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(
                participant__student__parent_links__parent=user.parent_profile,
                requested_from='parent',
            ).distinct()
        return self.queryset.none()

    @decorators.action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        confirmation = self.get_object()
        serializer = LessonConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        confirmation = confirm_lesson(
            user=request.user,
            confirmation=confirmation,
            comment=serializer.validated_data.get('comment', ''),
        )
        return response.Response(self.get_serializer(confirmation).data)

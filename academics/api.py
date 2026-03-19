from rest_framework import decorators, permissions, response, viewsets

from users.models import UserRole
from users.permissions import IsAdminOrRelatedAcademicObject, StaffWritePermission

from .models import (
    Lesson,
    LessonConfirmation,
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
    queryset = Lesson.objects.select_related('group', 'group__subject').prefetch_related('participants').all()
    serializer_class = LessonSerializer
    permission_classes = (StaffWritePermission, IsAdminOrRelatedAcademicObject)

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

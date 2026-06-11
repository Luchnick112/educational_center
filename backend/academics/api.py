from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from decimal import Decimal
from rest_framework import decorators, exceptions, permissions, response, status, viewsets

from users.models import UserRole
from users.permissions import IsAdminOrRelatedAcademicObject, IsAdminUserRole, StaffWritePermission

from .models import (
    GroupPricing,
    Lesson,
    LessonConfirmation,
    LessonParticipant,
    LessonRescheduleRequest,
    LessonStatus,
    StudentEnrollment,
    StudyGroup,
    Subject,
)
from .serializers import (
    AttendanceMarkSerializer,
    GroupPricingSerializer,
    GroupStudentsSyncSerializer,
    LessonCancelSerializer,
    LessonCompletionSerializer,
    LessonConfirmSerializer,
    LessonConfirmationSerializer,
    LessonRescheduleApplySerializer,
    LessonRescheduleRequestSerializer,
    LessonSerializer,
    StudentEnrollmentSerializer,
    StudyGroupSerializer,
    SubjectSerializer,
)
from .services import (
    apply_lesson_reschedule,
    cancel_lesson,
    complete_lesson,
    confirm_lesson,
    confirm_lesson_reschedule_by_parent,
    create_lesson_reschedule_request,
    mark_lesson_attendance,
)


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


class StaffOrTeacherAcademicWritePermission(permissions.BasePermission):
    """
    Allow teachers to create and manage their own groups/enrollments/lessons.
    """

    def has_permission(self, request, view):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            return bool(user and user.is_authenticated)

        if not user or not user.is_authenticated:
            return False

        if user.is_staff or user.role == UserRole.ADMIN:
            return True

        return user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile')


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().order_by('name')
    serializer_class = SubjectSerializer
    permission_classes = (StaffWritePermission,)


class StudyGroupViewSet(viewsets.ModelViewSet):
    queryset = StudyGroup.objects.select_related('subject', 'teacher', 'teacher__user').all()
    serializer_class = StudyGroupSerializer
    permission_classes = (StaffOrTeacherAcademicWritePermission, IsAdminOrRelatedAcademicObject)

    def get_permissions(self):
        if getattr(self, 'action', None) == 'destroy':
            return [IsAdminUserRole()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset.all()
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(teacher=user.teacher_profile)
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(enrollments__student=user.student_profile).distinct()
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(enrollments__student__parent_links__parent=user.parent_profile).distinct()
        return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        student_price = serializer.validated_data.get('student_price', Decimal('0.00'))
        teacher_rate = serializer.validated_data.get('teacher_rate', Decimal('0.00'))
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            serializer.save(
                teacher=user.teacher_profile,
                format='group',
                student_price=Decimal('0.00'),
                teacher_rate=Decimal('0.00'),
            )
            return
        serializer.save(format='group', student_price=student_price, teacher_rate=teacher_rate)

    def perform_update(self, serializer):
        user = self.request.user
        student_price = serializer.validated_data.get('student_price', serializer.instance.student_price)
        teacher_rate = serializer.validated_data.get('teacher_rate', serializer.instance.teacher_rate)
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            serializer.save(
                teacher=user.teacher_profile,
                format='group',
                student_price=serializer.instance.student_price,
                teacher_rate=serializer.instance.teacher_rate,
            )
            return
        serializer.save(format='group', student_price=student_price, teacher_rate=teacher_rate)

    def perform_destroy(self, instance):
        with transaction.atomic():
            instance.lessons.all().delete()
            instance.enrollments.all().delete()
            instance.delete()

    @decorators.action(detail=True, methods=['post'], url_path='students')
    def sync_students(self, request, pk=None):
        group = self.get_object()
        serializer = GroupStudentsSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        today = timezone.localdate()
        desired_ids = set(serializer.validated_data['student_ids'])
        existing = {enrollment.student_id: enrollment for enrollment in group.enrollments.all()}

        for student_id in desired_ids:
            enrollment = existing.get(student_id)
            if enrollment:
                if enrollment.status != 'active' or enrollment.end_date is not None:
                    enrollment.status = 'active'
                    enrollment.end_date = None
                    enrollment.save(update_fields=['status', 'end_date'])
                continue

            StudentEnrollment.objects.create(
                group=group,
                student_id=student_id,
                status='active',
                start_date=today,
            )

        for student_id, enrollment in existing.items():
            if enrollment.status == 'active' and student_id not in desired_ids:
                enrollment.status = 'cancelled'
                enrollment.end_date = today
                enrollment.save(update_fields=['status', 'end_date'])

        queryset = StudentEnrollment.objects.filter(group=group).select_related('group', 'student', 'student__user')
        return response.Response(StudentEnrollmentSerializer(queryset, many=True, context={'request': request}).data)


class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = StudentEnrollment.objects.select_related('group', 'student', 'student__user').all()
    serializer_class = StudentEnrollmentSerializer
    permission_classes = (StaffOrTeacherAcademicWritePermission, IsAdminOrRelatedAcademicObject)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset.all()
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(group__teacher=user.teacher_profile)
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(student__parent_links__parent=user.parent_profile).distinct()
        return self.queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        group = serializer.validated_data['group']
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            if group.teacher_id != user.teacher_profile.id:
                raise exceptions.PermissionDenied('You can only enroll students in your own groups.')
        serializer.save()

    def create(self, request, *args, **kwargs):
        group_id = request.data.get('group')
        student_id = request.data.get('student')
        if group_id is not None and student_id is not None:
            existing = self.get_queryset().filter(group_id=group_id, student_id=student_id).first()
            if existing:
                data = request.data.copy()
                if data.get('status') == 'active':
                    data['end_date'] = None
                serializer = self.get_serializer(existing, data=data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return response.Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        user = self.request.user
        group = serializer.validated_data.get('group', serializer.instance.group)
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            if group.teacher_id != user.teacher_profile.id:
                raise exceptions.PermissionDenied('You can only manage enrollments in your own groups.')
        serializer.save()


class GroupPricingViewSet(viewsets.ModelViewSet):
    queryset = GroupPricing.objects.select_related('group', 'group__subject', 'group__teacher').all()
    serializer_class = GroupPricingSerializer
    permission_classes = (IsAdminUserRole,)

    def get_queryset(self):
        queryset = self.queryset.order_by('group_id', '-effective_from', '-id')
        group_id = self.request.query_params.get('group')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset


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
            return self.queryset.all()
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
            if 'starts_at' in serializer.validated_data and serializer.validated_data['starts_at'] != instance.starts_at:
                raise exceptions.ValidationError({'starts_at': 'Use the reschedule request workflow to change lesson time.'})
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
            return self.queryset.all()
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


class LessonRescheduleRequestViewSet(viewsets.ModelViewSet):
    queryset = (
        LessonRescheduleRequest.objects.select_related(
            'lesson',
            'lesson__group',
            'lesson__group__teacher',
            'student',
            'student__user',
            'requested_by',
            'parent_confirmed_by',
            'applied_by',
        )
        .all()
    )
    serializer_class = LessonRescheduleRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        if user.is_staff or user.role == UserRole.ADMIN:
            pass
        elif user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            queryset = queryset.filter(lesson__group__teacher=user.teacher_profile)
        elif user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            queryset = queryset.filter(student=user.student_profile)
        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            queryset = queryset.filter(student__parent_links__parent=user.parent_profile).distinct()
        else:
            queryset = queryset.none()

        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset.order_by('-created_at', '-id')

    def perform_create(self, serializer):
        reschedule_request = create_lesson_reschedule_request(
            user=self.request.user,
            lesson=serializer.validated_data['lesson'],
            requested_starts_at=serializer.validated_data.get('requested_starts_at'),
            reason=serializer.validated_data.get('reason', ''),
        )
        serializer.instance = reschedule_request

    @decorators.action(detail=True, methods=['post'], url_path='confirm-parent')
    def confirm_parent(self, request, pk=None):
        reschedule_request = confirm_lesson_reschedule_by_parent(
            user=request.user,
            reschedule_request=self.get_object(),
        )
        return response.Response(self.get_serializer(reschedule_request).data)

    @decorators.action(detail=True, methods=['post'], url_path='apply')
    def apply(self, request, pk=None):
        serializer = LessonRescheduleApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reschedule_request = apply_lesson_reschedule(
            user=request.user,
            reschedule_request=self.get_object(),
            starts_at=serializer.validated_data['starts_at'],
            teacher_comment=serializer.validated_data.get('teacher_comment', ''),
        )
        return response.Response(self.get_serializer(reschedule_request).data)

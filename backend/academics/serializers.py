from rest_framework import serializers

from users.models import StudentParentRelation, UserRole

from .models import (
    AttendanceStatus,
    Lesson,
    LessonConfirmation,
    LessonParticipant,
    LessonStatus,
    StudentEnrollment,
    StudyGroup,
    Subject,
)

DATE_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DD'}
DATETIME_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DDTHH:MM:SSZ'}


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'description')


class StudyGroupSerializer(serializers.ModelSerializer):
    def _get_effective_student_price_for_student_ids(self, group: StudyGroup, student_ids: list[int]):
        if not student_ids:
            return group.student_price
        enrollment = (
            StudentEnrollment.objects.filter(group=group, student_id__in=student_ids)
            .order_by('-id')
            .first()
        )
        return (enrollment.student_price if enrollment else group.student_price)

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return rep

        if user.is_staff or getattr(user, 'role', None) == UserRole.ADMIN:
            return rep

        role = getattr(user, 'role', None)
        if role == UserRole.TEACHER:
            rep.pop('student_price', None)
            return rep

        if role == UserRole.STUDENT:
            rep.pop('teacher_rate', None)
            student_ids = [getattr(user.student_profile, 'id', None)] if hasattr(user, 'student_profile') else []
            student_ids = [sid for sid in student_ids if sid is not None]
            value = self._get_effective_student_price_for_student_ids(instance, student_ids)
            rep['student_price'] = self.fields['student_price'].to_representation(value)
            return rep

        if role == UserRole.PARENT:
            rep.pop('teacher_rate', None)
            if hasattr(user, 'parent_profile'):
                student_ids = list(
                    StudentParentRelation.objects.filter(
                        parent=user.parent_profile,
                        is_financial_contact=True,
                    ).values_list('student_id', flat=True)
                )
            else:
                student_ids = []
            value = self._get_effective_student_price_for_student_ids(instance, student_ids)
            rep['student_price'] = self.fields['student_price'].to_representation(value)
            return rep

        return rep

    class Meta:
        model = StudyGroup
        fields = (
            'id',
            'name',
            'subject',
            'teacher',
            'format',
            'capacity',
            'student_price',
            'teacher_rate',
            'is_active',
        )
        read_only_fields = ('name',)


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(style=DATE_INPUT_STYLE)
    end_date = serializers.DateField(required=False, allow_null=True, style=DATE_INPUT_STYLE)

    class Meta:
        model = StudentEnrollment
        fields = (
            'id',
            'group',
            'student',
            'status',
            'start_date',
            'end_date',
            'student_price_override',
            'teacher_rate_override',
        )


class LessonParticipantSerializer(serializers.ModelSerializer):
    teacher_id = serializers.IntegerField(source='lesson.group.teacher_id', read_only=True)
    teacher_last_name = serializers.CharField(source='lesson.group.teacher.user.last_name', read_only=True)
    student_last_name = serializers.CharField(source='student.user.last_name', read_only=True)

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or not getattr(user, 'is_authenticated', False):
            rep.pop('teacher_id', None)
            rep.pop('teacher_last_name', None)
            rep.pop('student_last_name', None)
            rep.pop('payroll_amount', None)
            return rep

        if user.is_staff or getattr(user, 'role', None) == UserRole.ADMIN:
            return rep

        role = getattr(user, 'role', None)
        if role == UserRole.TEACHER:
            # Teachers should see their payroll amount, not the billed amount charged to parents/students.
            rep.pop('billed_amount', None)
        if role in {UserRole.STUDENT, UserRole.PARENT}:
            rep.pop('payroll_amount', None)

        rep.pop('teacher_id', None)
        rep.pop('teacher_last_name', None)
        rep.pop('student_last_name', None)
        return rep

    class Meta:
        model = LessonParticipant
        fields = (
            'id',
            'lesson',
            'enrollment',
            'student',
            'teacher_id',
            'teacher_last_name',
            'student_last_name',
            'attendance_status',
            'billed_amount',
            'payroll_amount',
        )
        read_only_fields = ('student', 'billed_amount', 'payroll_amount')


class LessonSerializer(serializers.ModelSerializer):
    starts_at = serializers.DateTimeField(style=DATETIME_INPUT_STYLE)
    participants = LessonParticipantSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit group choices based on role for create/update forms and OPTIONS metadata.
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            self.fields['group'].queryset = StudyGroup.objects.none()
            return

        if user.is_staff or getattr(user, 'role', None) == UserRole.ADMIN:
            self.fields['group'].queryset = StudyGroup.objects.all()
            return

        if getattr(user, 'role', None) == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            self.fields['group'].queryset = StudyGroup.objects.filter(teacher=user.teacher_profile)
            return

        self.fields['group'].queryset = StudyGroup.objects.none()

    class Meta:
        model = Lesson
        fields = (
            'id',
            'group',
            'starts_at',
            'status',
            'notes',
            'participants',
        )


class LessonConfirmationSerializer(serializers.ModelSerializer):
    confirmed_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)

    class Meta:
        model = LessonConfirmation
        fields = ('id', 'participant', 'requested_from', 'confirmer', 'status', 'confirmed_at', 'comment')


class AttendanceMarkSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField()
    attendance_status = serializers.ChoiceField(choices=AttendanceStatus.choices)


class LessonCompletionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)


class LessonCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True, allow_blank=False)


class LessonConfirmSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)

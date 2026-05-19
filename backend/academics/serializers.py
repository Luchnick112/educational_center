from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from users.models import StudentParentRelation, UserRole

from .models import (
    AttendanceStatus,
    GroupPricing,
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
            student_price, _ = group.get_effective_pricing(timezone.now())
            return student_price
        enrollment = (
            StudentEnrollment.objects.filter(group=group, student_id__in=student_ids)
            .order_by('-id')
            .first()
        )
        if enrollment and enrollment.student_price_override is not None:
            return enrollment.student_price_override
        student_price, _ = group.get_effective_pricing(timezone.now())
        return student_price

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
            _, teacher_rate = instance.get_effective_pricing(timezone.now())
            rep['teacher_rate'] = self.fields['teacher_rate'].to_representation(teacher_rate)
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

        student_price, teacher_rate = instance.get_effective_pricing(timezone.now())
        rep['student_price'] = self.fields['student_price'].to_representation(student_price)
        rep['teacher_rate'] = self.fields['teacher_rate'].to_representation(teacher_rate)
        return rep

    class Meta:
        model = StudyGroup
        fields = (
            'id',
            'name',
            'subject',
            'teacher',
            'capacity',
            'student_price',
            'teacher_rate',
            'is_active',
        )
        read_only_fields = ('name',)
        extra_kwargs = {
            'student_price': {'required': False},
            'teacher_rate': {'required': False},
        }


class StudentEnrollmentSerializer(serializers.ModelSerializer):
    start_date = serializers.DateField(style=DATE_INPUT_STYLE)
    end_date = serializers.DateField(required=False, allow_null=True, style=DATE_INPUT_STYLE)
    student_first_name = serializers.CharField(source='student.user.first_name', read_only=True)
    student_last_name = serializers.CharField(source='student.user.last_name', read_only=True)
    student_email = serializers.EmailField(source='student.user.email', read_only=True)
    student_telegram_username = serializers.CharField(source='student.user.telegram_username', read_only=True)

    class Meta:
        model = StudentEnrollment
        fields = (
            'id',
            'group',
            'student',
            'student_first_name',
            'student_last_name',
            'student_email',
            'student_telegram_username',
            'status',
            'start_date',
            'end_date',
            'student_price_override',
            'teacher_rate_override',
        )


class GroupStudentsSyncSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )


class GroupPricingSerializer(serializers.ModelSerializer):
    effective_from = serializers.DateTimeField(style=DATETIME_INPUT_STYLE)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = GroupPricing
        fields = (
            'id',
            'group',
            'group_name',
            'student_price',
            'teacher_rate',
            'effective_from',
            'created_at',
        )
        read_only_fields = ('created_at',)


class LessonParticipantSerializer(serializers.ModelSerializer):
    teacher_id = serializers.IntegerField(source='lesson.group.teacher_id', read_only=True)
    student_first_name = serializers.CharField(source='student.user.first_name', read_only=True)
    teacher_last_name = serializers.CharField(source='lesson.group.teacher.user.last_name', read_only=True)
    student_last_name = serializers.CharField(source='student.user.last_name', read_only=True)

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or not getattr(user, 'is_authenticated', False):
            rep.pop('teacher_id', None)
            rep.pop('teacher_last_name', None)
            rep.pop('student_first_name', None)
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
        rep.pop('student_first_name', None)
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
            'student_first_name',
            'teacher_last_name',
            'student_last_name',
            'attendance_status',
            'billed_amount',
            'payroll_amount',
        )
        read_only_fields = ('student', 'billed_amount', 'payroll_amount')


class LessonParticipantAmountUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    billed_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    payroll_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)


class LessonSerializer(serializers.ModelSerializer):
    starts_at = serializers.DateTimeField(style=DATETIME_INPUT_STYLE)
    participants = LessonParticipantSerializer(many=True, read_only=True)
    participant_updates = LessonParticipantAmountUpdateSerializer(many=True, write_only=True, required=False)
    payroll_amount = serializers.SerializerMethodField()
    billed_amount = serializers.SerializerMethodField()

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

    def get_payroll_amount(self, instance):
        value = getattr(instance, 'payroll_amount_total', None)
        if value is None:
            value = sum((participant.payroll_amount for participant in instance.participants.all()), Decimal('0.00'))
        return f'{value:.2f}'

    def get_billed_amount(self, instance):
        value = getattr(instance, 'billed_amount_total', None)
        if value is None:
            value = sum((participant.billed_amount for participant in instance.participants.all()), Decimal('0.00'))
        return f'{value:.2f}'

    def update(self, instance, validated_data):
        participant_updates = validated_data.pop('participant_updates', [])
        participants = {}

        if participant_updates:
            request = self.context.get('request')
            user = getattr(request, 'user', None)
            if not user or not (getattr(user, 'is_staff', False) or getattr(user, 'role', None) == UserRole.ADMIN):
                raise serializers.ValidationError({'participant_updates': 'Only admins can update participant amounts.'})

            participants = {p.id: p for p in instance.participants.filter(id__in=[item['id'] for item in participant_updates])}
            for item in participant_updates:
                if item['id'] not in participants:
                    raise serializers.ValidationError({'participant_updates': f'Participant {item["id"]} does not belong to this lesson.'})

        with transaction.atomic():
            if participant_updates:
                for item in participant_updates:
                    participant = participants[item['id']]
                    update_fields = []
                    if 'billed_amount' in item:
                        participant.billed_amount = item['billed_amount']
                        update_fields.append('billed_amount')
                    if 'payroll_amount' in item:
                        participant.payroll_amount = item['payroll_amount']
                        update_fields.append('payroll_amount')
                    if update_fields:
                        participant.save(update_fields=update_fields)

            instance = super().update(instance, validated_data)

            if hasattr(instance, '_prefetched_objects_cache'):
                instance._prefetched_objects_cache.pop('participants', None)

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            rep.pop('payroll_amount', None)
            rep.pop('billed_amount', None)
            return rep

        role = getattr(user, 'role', None)
        if not (user.is_staff or role in {UserRole.ADMIN, UserRole.TEACHER}):
            rep.pop('payroll_amount', None)
        if not (user.is_staff or role == UserRole.ADMIN):
            rep.pop('billed_amount', None)

        return rep

    class Meta:
        model = Lesson
        fields = (
            'id',
            'group',
            'starts_at',
            'payroll_amount',
            'billed_amount',
            'status',
            'notes',
            'participants',
            'participant_updates',
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

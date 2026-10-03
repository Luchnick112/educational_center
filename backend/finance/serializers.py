from decimal import Decimal

from rest_framework import serializers

from users.models import TeacherProfile

from .models import LessonTeacherPayout, ParentCharge, StudentPayment, TeacherPayment, TeacherPayout

DATE_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DD'}
DATETIME_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DDTHH:MM:SSZ'}


def profile_label(profile) -> str:
    user = profile.user
    full_name = user.get_full_name().strip()
    return full_name or user.telegram_username or user.email or f'#{profile.id}'


class ParentChargeSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(required=False, allow_null=True, style=DATE_INPUT_STYLE)
    issued_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    paid_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    period_start_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    period_end_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    group_name = serializers.SerializerMethodField()
    invoice_date = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()
    lesson_starts_at = serializers.DateTimeField(source='participant.lesson.starts_at', read_only=True)

    class Meta:
        model = ParentCharge
        fields = (
            'id',
            'participant',
            'parent',
            'parent_name',
            'student',
            'student_name',
            'group_name',
            'invoice_date',
            'lesson_starts_at',
            'amount',
            'billing_period',
            'lesson_count',
            'period_start_at',
            'period_end_at',
            'status',
            'due_date',
            'issued_at',
            'paid_at',
        )

    def get_parent_name(self, instance):
        return profile_label(instance.parent)

    def get_student_name(self, instance):
        return profile_label(instance.student)

    def get_group_name(self, instance):
        return instance.participant.lesson.group.name

    def get_invoice_date(self, instance):
        value = instance.period_end_at or instance.issued_at or instance.participant.lesson.starts_at
        return value.isoformat() if value else None


class TeacherPayoutSerializer(serializers.ModelSerializer):
    payout_type = serializers.SerializerMethodField()
    approved_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    paid_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    period_start_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    period_end_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    group_name = serializers.SerializerMethodField()
    invoice_date = serializers.SerializerMethodField()
    lesson = serializers.IntegerField(source='participant.lesson_id', read_only=True)
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    lesson_starts_at = serializers.DateTimeField(source='participant.lesson.starts_at', read_only=True)

    class Meta:
        model = TeacherPayout
        fields = (
            'id',
            'payout_type',
            'participant',
            'lesson',
            'teacher',
            'teacher_name',
            'student_name',
            'group_name',
            'invoice_date',
            'lesson_starts_at',
            'amount',
            'billing_period',
            'lesson_count',
            'period_start_at',
            'period_end_at',
            'status',
            'approved_at',
            'paid_at',
        )

    def get_student_name(self, instance):
        return profile_label(instance.participant.student)

    def get_teacher_name(self, instance):
        return profile_label(instance.teacher)

    def get_group_name(self, instance):
        return instance.participant.lesson.group.name

    def get_invoice_date(self, instance):
        value = instance.period_end_at or instance.participant.lesson.starts_at
        return value.isoformat() if value else None

    def get_payout_type(self, instance):
        return 'participant'


class LessonTeacherPayoutSerializer(serializers.ModelSerializer):
    payout_type = serializers.SerializerMethodField()
    participant = serializers.SerializerMethodField()
    lesson = serializers.IntegerField(source='lesson_id', read_only=True)
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    invoice_date = serializers.SerializerMethodField()
    lesson_starts_at = serializers.DateTimeField(source='lesson.starts_at', read_only=True)
    approved_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    paid_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    period_start_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    period_end_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)

    class Meta:
        model = LessonTeacherPayout
        fields = (
            'id',
            'payout_type',
            'participant',
            'lesson',
            'teacher',
            'teacher_name',
            'student_name',
            'group_name',
            'invoice_date',
            'lesson_starts_at',
            'amount',
            'billing_period',
            'lesson_count',
            'period_start_at',
            'period_end_at',
            'status',
            'approved_at',
            'paid_at',
        )

    def get_payout_type(self, instance):
        return 'lesson'

    def get_participant(self, instance):
        return None

    def get_student_name(self, instance):
        return 'За урок'

    def get_teacher_name(self, instance):
        return profile_label(instance.teacher)

    def get_group_name(self, instance):
        return instance.lesson.group.name

    def get_invoice_date(self, instance):
        value = instance.period_end_at or instance.lesson.starts_at
        return value.isoformat() if value else None


class StudentPaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    paid_at = serializers.DateField(style=DATE_INPUT_STYLE)
    created_at = serializers.DateTimeField(read_only=True, style=DATETIME_INPUT_STYLE)

    class Meta:
        model = StudentPayment
        fields = ('id', 'student', 'student_name', 'amount', 'paid_at', 'comment', 'created_at', 'created_by')
        read_only_fields = ('created_by', 'created_at')

    def get_student_name(self, instance):
        return profile_label(instance.student)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value


class TeacherPaymentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    paid_at = serializers.DateField(style=DATE_INPUT_STYLE)
    created_at = serializers.DateTimeField(read_only=True, style=DATETIME_INPUT_STYLE)

    class Meta:
        model = TeacherPayment
        fields = ('id', 'teacher', 'teacher_name', 'amount', 'paid_at', 'comment', 'created_at', 'created_by')
        read_only_fields = ('created_by', 'created_at')

    def get_teacher_name(self, instance):
        return profile_label(instance.teacher)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value


class TeacherPaymentAllocationRequestSerializer(serializers.Serializer):
    teacher = serializers.PrimaryKeyRelatedField(queryset=TeacherProfile.objects.all())
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    paid_at = serializers.DateField(required=False)
    comment = serializers.CharField(required=False, allow_blank=True)
    selected_payouts = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )

    def validate_selected_payouts(self, value):
        normalized = []
        for item in value:
            payout_type = item.get('payout_type')
            payout_id = item.get('id')
            if payout_type not in {'participant', 'lesson'}:
                raise serializers.ValidationError('Invalid payout type.')
            if not isinstance(payout_id, int) or payout_id < 1:
                raise serializers.ValidationError('Payout id must be a positive integer.')
            normalized.append({'payout_type': payout_type, 'id': payout_id})
        return normalized


class ParentChargeIssueSerializer(serializers.Serializer):
    due_date = serializers.DateField(required=False, style=DATE_INPUT_STYLE)


class ParentChargeMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)


class TeacherPayoutApproveSerializer(serializers.Serializer):
    approved_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)


class TeacherPayoutMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)

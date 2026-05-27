from rest_framework import serializers

from .models import ParentCharge, StudentPayment, TeacherPayment, TeacherPayout

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
            'lesson_starts_at',
            'amount',
            'status',
            'due_date',
            'issued_at',
            'paid_at',
        )

    def get_parent_name(self, instance):
        return profile_label(instance.parent)

    def get_student_name(self, instance):
        return profile_label(instance.student)


class TeacherPayoutSerializer(serializers.ModelSerializer):
    approved_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    paid_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    lesson = serializers.IntegerField(source='participant.lesson_id', read_only=True)
    student_name = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()
    lesson_starts_at = serializers.DateTimeField(source='participant.lesson.starts_at', read_only=True)

    class Meta:
        model = TeacherPayout
        fields = (
            'id',
            'participant',
            'lesson',
            'teacher',
            'teacher_name',
            'student_name',
            'lesson_starts_at',
            'amount',
            'status',
            'approved_at',
            'paid_at',
        )

    def get_student_name(self, instance):
        return profile_label(instance.participant.student)

    def get_teacher_name(self, instance):
        return profile_label(instance.teacher)


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


class ParentChargeIssueSerializer(serializers.Serializer):
    due_date = serializers.DateField(required=False, style=DATE_INPUT_STYLE)


class ParentChargeMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)


class TeacherPayoutApproveSerializer(serializers.Serializer):
    approved_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)


class TeacherPayoutMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)

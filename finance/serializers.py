from rest_framework import serializers

from .models import ParentCharge, TeacherPayout

DATE_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DD'}
DATETIME_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DDTHH:MM:SSZ'}


class ParentChargeSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(required=False, allow_null=True, style=DATE_INPUT_STYLE)
    issued_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    paid_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)

    class Meta:
        model = ParentCharge
        fields = ('id', 'participant', 'parent', 'student', 'amount', 'status', 'due_date', 'issued_at', 'paid_at')


class TeacherPayoutSerializer(serializers.ModelSerializer):
    approved_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)
    paid_at = serializers.DateTimeField(required=False, allow_null=True, style=DATETIME_INPUT_STYLE)

    class Meta:
        model = TeacherPayout
        fields = ('id', 'participant', 'teacher', 'amount', 'status', 'approved_at', 'paid_at')


class ParentChargeIssueSerializer(serializers.Serializer):
    due_date = serializers.DateField(required=False, style=DATE_INPUT_STYLE)


class ParentChargeMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)


class TeacherPayoutApproveSerializer(serializers.Serializer):
    approved_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)


class TeacherPayoutMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False, style=DATETIME_INPUT_STYLE)

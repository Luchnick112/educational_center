from rest_framework import serializers

from .models import ParentCharge, TeacherPayout


class ParentChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentCharge
        fields = ('id', 'participant', 'parent', 'student', 'amount', 'status', 'due_date', 'issued_at', 'paid_at')


class TeacherPayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherPayout
        fields = ('id', 'participant', 'teacher', 'amount', 'status', 'approved_at', 'paid_at')


class ParentChargeIssueSerializer(serializers.Serializer):
    due_date = serializers.DateField(required=False)


class ParentChargeMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False)


class TeacherPayoutApproveSerializer(serializers.Serializer):
    approved_at = serializers.DateTimeField(required=False)


class TeacherPayoutMarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateTimeField(required=False)

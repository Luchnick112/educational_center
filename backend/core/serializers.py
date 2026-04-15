from rest_framework import serializers

from academics.serializers import LessonConfirmationSerializer, LessonSerializer
from finance.serializers import ParentChargeSerializer, TeacherPayoutSerializer
from users.serializers import ParentProfileSerializer, StudentProfileSerializer, UserSerializer


class MyLinkSerializer(serializers.Serializer):
    key = serializers.CharField()
    url = serializers.URLField()


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    telegram_username = serializers.CharField(allow_blank=True, required=False)
    email = serializers.EmailField(allow_blank=True)
    role = serializers.CharField()
    is_staff = serializers.BooleanField()
    # Discoverability: links to personal ("my") endpoints.
    my = MyLinkSerializer(many=True, required=False)


class MyPaymentsSerializer(serializers.Serializer):
    charges = ParentChargeSerializer(many=True)
    payouts = TeacherPayoutSerializer(many=True)


class EmptyObjectSerializer(serializers.Serializer):
    pass


class DashboardStatsSerializer(serializers.Serializer):
    active_enrollments = serializers.IntegerField(required=False)
    upcoming_lessons = serializers.IntegerField(required=False)
    pending_confirmations = serializers.IntegerField(required=False)
    children = serializers.IntegerField(required=False)
    open_charges = serializers.IntegerField(required=False)
    groups = serializers.IntegerField(required=False)
    scheduled_lessons = serializers.IntegerField(required=False)
    pending_payouts = serializers.IntegerField(required=False)
    users = serializers.IntegerField(required=False)


class DashboardSerializer(serializers.Serializer):
    user = UserSerializer()
    role = serializers.CharField()
    stats = DashboardStatsSerializer()

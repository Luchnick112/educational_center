from rest_framework import serializers

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


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'description')


class StudyGroupSerializer(serializers.ModelSerializer):
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


class StudentEnrollmentSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = LessonParticipant
        fields = (
            'id',
            'lesson',
            'enrollment',
            'student',
            'attendance_status',
            'billed_amount',
            'payroll_amount',
        )
        read_only_fields = ('student', 'billed_amount', 'payroll_amount')


class LessonSerializer(serializers.ModelSerializer):
    participants = LessonParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = (
            'id',
            'group',
            'title',
            'starts_at',
            'ends_at',
            'status',
            'homework',
            'notes',
            'participants',
        )


class LessonConfirmationSerializer(serializers.ModelSerializer):
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

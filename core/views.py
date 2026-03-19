from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Lesson, LessonConfirmation
from academics.serializers import LessonConfirmationSerializer, LessonSerializer
from finance.models import ParentCharge, TeacherPayout
from finance.serializers import ParentChargeSerializer, TeacherPayoutSerializer
from users.models import StudentProfile, UserRole
from users.serializers import ParentProfileSerializer, StudentProfileSerializer
from .serializers import EmptyObjectSerializer, MeSerializer, MyPaymentsSerializer


class MeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=MeSerializer)
    def get(self, request):
        return Response(
            {
                'id': request.user.id,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'role': request.user.role,
                'is_staff': request.user.is_staff,
            }
        )


class MyLessonsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=LessonSerializer(many=True))
    def get(self, request):
        user = request.user
        queryset = Lesson.objects.none()

        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            queryset = Lesson.objects.filter(participants__student=user.student_profile).distinct()
        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            queryset = Lesson.objects.filter(
                participants__student__parent_links__parent=user.parent_profile,
            ).distinct()
        elif user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            queryset = Lesson.objects.filter(group__teacher=user.teacher_profile)
        elif user.is_staff or user.role == UserRole.ADMIN:
            queryset = Lesson.objects.all()

        serializer = LessonSerializer(queryset.order_by('starts_at')[:20], many=True)
        return Response(serializer.data)


class MyChildrenView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=StudentProfileSerializer(many=True))
    def get(self, request):
        user = request.user
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            students = [link.student for link in user.parent_profile.student_links.select_related('student', 'student__user')]
            serializer = StudentProfileSerializer(students, many=True)
            return Response(serializer.data)

        if user.is_staff or user.role == UserRole.ADMIN:
            serializer = StudentProfileSerializer(StudentProfile.objects.select_related('user').all(), many=True)
            return Response(serializer.data)

        return Response([])


class MyPaymentsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=MyPaymentsSerializer)
    def get(self, request):
        user = request.user
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            charges = ParentCharge.objects.filter(parent=user.parent_profile).order_by('-issued_at')
            return Response(
                {
                    'charges': ParentChargeSerializer(charges, many=True).data,
                    'payouts': [],
                }
            )
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            payouts = TeacherPayout.objects.filter(teacher=user.teacher_profile).order_by('-id')
            return Response(
                {
                    'charges': [],
                    'payouts': TeacherPayoutSerializer(payouts, many=True).data,
                }
            )
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            charges = ParentCharge.objects.filter(student=user.student_profile).order_by('-issued_at')
            return Response(
                {
                    'charges': ParentChargeSerializer(charges, many=True).data,
                    'payouts': [],
                }
            )
        return Response({'charges': [], 'payouts': []})


class MyConfirmationsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=LessonConfirmationSerializer(many=True))
    def get(self, request):
        user = request.user
        queryset = LessonConfirmation.objects.none()

        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            queryset = LessonConfirmation.objects.filter(
                participant__student=user.student_profile,
                requested_from='student',
            )
        elif user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            queryset = LessonConfirmation.objects.filter(
                participant__student__parent_links__parent=user.parent_profile,
                requested_from='parent',
            ).distinct()
        elif user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            queryset = LessonConfirmation.objects.filter(
                participant__lesson__group__teacher=user.teacher_profile,
                requested_from='teacher',
            )
        elif user.is_staff or user.role == UserRole.ADMIN:
            queryset = LessonConfirmation.objects.all()

        serializer = LessonConfirmationSerializer(queryset.order_by('-id')[:50], many=True)
        return Response(serializer.data)


class MyChildrenSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        responses={
            200: ParentProfileSerializer,
            204: EmptyObjectSerializer,
        }
    )
    def get(self, request):
        user = request.user
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            serializer = ParentProfileSerializer(user.parent_profile)
            return Response(serializer.data)
        return Response({})

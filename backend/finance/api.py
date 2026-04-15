from rest_framework import decorators, permissions, response, viewsets

from users.models import UserRole
from users.permissions import IsAdminOrRelatedAcademicObject, StaffWritePermission

from .models import ParentCharge, TeacherPayout
from .serializers import (
    ParentChargeIssueSerializer,
    ParentChargeMarkPaidSerializer,
    ParentChargeSerializer,
    TeacherPayoutApproveSerializer,
    TeacherPayoutMarkPaidSerializer,
    TeacherPayoutSerializer,
)
from .services import (
    approve_teacher_payout,
    issue_parent_charge,
    mark_parent_charge_paid,
    mark_teacher_payout_paid,
)


class ParentChargeViewSet(viewsets.ModelViewSet):
    queryset = ParentCharge.objects.select_related('parent', 'student', 'participant').all()
    serializer_class = ParentChargeSerializer
    permission_classes = (StaffWritePermission, IsAdminOrRelatedAcademicObject)

    def get_permissions(self):
        if getattr(self, 'action', None) in {'issue', 'mark_paid'}:
            return [permissions.IsAuthenticated(), IsAdminOrRelatedAcademicObject()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(parent=user.parent_profile)
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)
        return self.queryset.none()

    @decorators.action(detail=True, methods=['post'], url_path='issue')
    def issue(self, request, pk=None):
        charge = self.get_object()
        serializer = ParentChargeIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        charge = issue_parent_charge(
            user=request.user,
            charge=charge,
            due_date=serializer.validated_data.get('due_date'),
        )
        return response.Response(self.get_serializer(charge).data)

    @decorators.action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        charge = self.get_object()
        serializer = ParentChargeMarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        charge = mark_parent_charge_paid(
            user=request.user,
            charge=charge,
            paid_at=serializer.validated_data.get('paid_at'),
        )
        return response.Response(self.get_serializer(charge).data)


class TeacherPayoutViewSet(viewsets.ModelViewSet):
    queryset = TeacherPayout.objects.select_related('teacher', 'participant').all()
    serializer_class = TeacherPayoutSerializer
    permission_classes = (StaffWritePermission, IsAdminOrRelatedAcademicObject)

    def get_permissions(self):
        if getattr(self, 'action', None) in {'approve', 'mark_paid'}:
            return [permissions.IsAuthenticated(), IsAdminOrRelatedAcademicObject()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(teacher=user.teacher_profile)
        return self.queryset.none()

    @decorators.action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        payout = self.get_object()
        serializer = TeacherPayoutApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payout = approve_teacher_payout(
            user=request.user,
            payout=payout,
            approved_at=serializer.validated_data.get('approved_at'),
        )
        return response.Response(self.get_serializer(payout).data)

    @decorators.action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        payout = self.get_object()
        serializer = TeacherPayoutMarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payout = mark_teacher_payout_paid(
            user=request.user,
            payout=payout,
            paid_at=serializer.validated_data.get('paid_at'),
        )
        return response.Response(self.get_serializer(payout).data)

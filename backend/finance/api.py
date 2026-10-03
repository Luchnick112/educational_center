from rest_framework import decorators, permissions, response, viewsets

from users.models import UserRole
from users.permissions import IsAdminOrRelatedAcademicObject, StaffWritePermission

from .models import LessonTeacherPayout, ParentCharge, StudentPayment, TeacherPayment, TeacherPayout
from .serializers import (
    LessonTeacherPayoutSerializer,
    ParentChargeIssueSerializer,
    ParentChargeMarkPaidSerializer,
    ParentChargeSerializer,
    StudentPaymentSerializer,
    TeacherPayoutApproveSerializer,
    TeacherPayoutMarkPaidSerializer,
    TeacherPayoutSerializer,
    TeacherPaymentAllocationRequestSerializer,
    TeacherPaymentSerializer,
)
from .services import (
    approve_teacher_payout,
    issue_parent_charge,
    mark_parent_charge_paid,
    mark_teacher_payout_paid,
    allocate_teacher_payment,
    preview_teacher_payment,
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
    queryset = TeacherPayout.objects.select_related('teacher', 'participant__lesson__group').all()
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


class LessonTeacherPayoutViewSet(viewsets.ModelViewSet):
    queryset = LessonTeacherPayout.objects.select_related('teacher', 'lesson__group').all()
    serializer_class = LessonTeacherPayoutSerializer
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


class StudentPaymentViewSet(viewsets.ModelViewSet):
    queryset = StudentPayment.objects.select_related('student__user', 'created_by').order_by('-paid_at', '-id')
    serializer_class = StudentPaymentSerializer
    permission_classes = (permissions.IsAuthenticated, StaffWritePermission)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
            return self.queryset.filter(student=user.student_profile)
        if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
            return self.queryset.filter(student__parent_links__parent=user.parent_profile).distinct()
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TeacherPaymentViewSet(viewsets.ModelViewSet):
    queryset = TeacherPayment.objects.select_related('teacher__user', 'created_by').order_by('-paid_at', '-id')
    serializer_class = TeacherPaymentSerializer
    permission_classes = (permissions.IsAuthenticated, StaffWritePermission)

    def _allocation_response(self, teacher, amount, allocation, payment=None):
        def serialize_payouts(payouts):
            serialized = []
            for payout_type, payout in payouts:
                serializer_class = TeacherPayoutSerializer if payout_type == 'participant' else LessonTeacherPayoutSerializer
                serialized.append(serializer_class(payout).data)
            return serialized

        serialized_payouts = serialize_payouts(allocation['payouts'])
        serialized_candidates = serialize_payouts(allocation['candidates'])

        payload = {
            'teacher': teacher.id,
            'amount': f'{amount:.2f}',
            'allocated_amount': f"{allocation['allocated_amount']:.2f}",
            'advance_amount': f"{allocation['advance_amount']:.2f}",
            'selected_count': len(allocation['payouts']),
            'payouts': serialized_payouts,
            'candidates': serialized_candidates,
        }
        if payment is not None:
            payload['payment'] = TeacherPaymentSerializer(payment).data
        return payload

    @decorators.action(detail=False, methods=['post'], url_path='preview-allocation')
    def preview_allocation(self, request):
        serializer = TeacherPaymentAllocationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        teacher = serializer.validated_data['teacher']
        amount = serializer.validated_data['amount']
        allocation = preview_teacher_payment(
            user=request.user,
            teacher_id=teacher.id,
            amount=amount,
            selected_payouts=serializer.validated_data.get('selected_payouts'),
        )
        return response.Response(self._allocation_response(teacher, amount, allocation))

    @decorators.action(detail=False, methods=['post'], url_path='allocate')
    def allocate(self, request):
        serializer = TeacherPaymentAllocationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        teacher = serializer.validated_data['teacher']
        amount = serializer.validated_data['amount']
        payment, allocation = allocate_teacher_payment(
            user=request.user,
            teacher_id=teacher.id,
            amount=amount,
            paid_at=serializer.validated_data.get('paid_at'),
            comment=serializer.validated_data.get('comment', ''),
            selected_payouts=serializer.validated_data.get('selected_payouts'),
        )
        return response.Response(self._allocation_response(teacher, amount, allocation, payment), status=201)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == UserRole.ADMIN:
            return self.queryset
        if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
            return self.queryset.filter(teacher=user.teacher_profile)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

from django.utils import timezone
from rest_framework import exceptions

from users.models import UserRole

from .models import ChargeStatus, ParentCharge, PayoutStatus, StudentPayment, TeacherPayment, TeacherPayout


def ensure_finance_admin(user, action_label: str) -> None:
    if user.is_staff or user.role == UserRole.ADMIN:
        return
    raise exceptions.PermissionDenied(f'Only admins can {action_label}.')


def issue_parent_charge(*, user, charge: ParentCharge, due_date=None) -> ParentCharge:
    ensure_finance_admin(user, 'issue charges')
    if charge.status != ChargeStatus.DRAFT:
        raise exceptions.ValidationError({'detail': 'Only draft charges can be issued.'})

    charge.status = ChargeStatus.ISSUED
    if due_date:
        charge.due_date = due_date
        charge.save(update_fields=['status', 'due_date'])
    else:
        charge.save(update_fields=['status'])
    return charge


def mark_parent_charge_paid(*, user, charge: ParentCharge, paid_at=None) -> ParentCharge:
    ensure_finance_admin(user, 'mark charges as paid')
    if charge.status not in {ChargeStatus.DRAFT, ChargeStatus.ISSUED}:
        raise exceptions.ValidationError({'detail': 'Only draft or issued charges can be paid.'})

    charge.status = ChargeStatus.PAID
    charge.paid_at = paid_at or timezone.now()
    charge.save(update_fields=['status', 'paid_at'])
    StudentPayment.objects.get_or_create(
        student=charge.student,
        amount=charge.amount,
        paid_at=charge.paid_at.date(),
        comment=f'Charge #{charge.id}',
        defaults={'created_by': user},
    )
    return charge


def approve_teacher_payout(*, user, payout: TeacherPayout, approved_at=None) -> TeacherPayout:
    ensure_finance_admin(user, 'approve payouts')
    if payout.status != PayoutStatus.DRAFT:
        raise exceptions.ValidationError({'detail': 'Only draft payouts can be approved.'})

    payout.status = PayoutStatus.APPROVED
    payout.approved_at = approved_at or timezone.now()
    payout.save(update_fields=['status', 'approved_at'])
    return payout


def mark_teacher_payout_paid(*, user, payout: TeacherPayout, paid_at=None) -> TeacherPayout:
    ensure_finance_admin(user, 'mark payouts as paid')
    if payout.status not in {PayoutStatus.DRAFT, PayoutStatus.APPROVED}:
        raise exceptions.ValidationError({'detail': 'Only draft or approved payouts can be paid.'})

    payout.status = PayoutStatus.PAID
    payout.paid_at = paid_at or timezone.now()
    update_fields = ['status', 'paid_at']
    if payout.approved_at is None:
        payout.approved_at = timezone.now()
        update_fields.append('approved_at')
    payout.save(update_fields=update_fields)
    TeacherPayment.objects.get_or_create(
        teacher=payout.teacher,
        amount=payout.amount,
        paid_at=payout.paid_at.date(),
        comment=f'Payout #{payout.id}',
        defaults={'created_by': user},
    )
    return payout

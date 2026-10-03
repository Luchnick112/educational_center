from decimal import Decimal
from datetime import datetime, time

from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions

from users.models import UserRole

from .models import (
    ChargeStatus,
    LessonTeacherPayout,
    ParentCharge,
    PayoutStatus,
    StudentPayment,
    TeacherPayment,
    TeacherPayout,
)


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
        paid_at=timezone.localdate(charge.paid_at),
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
        paid_at=timezone.localdate(payout.paid_at),
        comment=f'Payout #{payout.id}',
        defaults={'created_by': user},
    )
    return payout


def _teacher_payout_candidates(teacher_id, *, for_update=False):
    payout_querysets = [
        (
            'participant',
            TeacherPayout.objects.select_related(
                'participant__lesson__group',
                'participant__student__user',
            ).filter(
                teacher_id=teacher_id,
                status__in=(PayoutStatus.DRAFT, PayoutStatus.APPROVED),
            ),
        ),
        (
            'lesson',
            LessonTeacherPayout.objects.select_related(
                'lesson__group',
            ).filter(
                teacher_id=teacher_id,
                status__in=(PayoutStatus.DRAFT, PayoutStatus.APPROVED),
            ),
        ),
    ]
    candidates = []
    for payout_type, queryset in payout_querysets:
        if for_update:
            queryset = queryset.select_for_update()
        candidates.extend((payout_type, payout) for payout in queryset)

    def sort_key(item):
        payout_type, payout = item
        lesson_starts_at = (
            payout.participant.lesson.starts_at
            if payout_type == 'participant'
            else payout.lesson.starts_at
        )
        return (
            payout.period_end_at or lesson_starts_at or timezone.make_aware(datetime.min),
            payout.id,
            payout_type,
        )

    return sorted(candidates, key=sort_key)


def _build_teacher_payment_allocation(*, amount, candidates, selected_payouts=None):
    if selected_payouts is None:
        remaining = amount
        selected = []
        for payout_type, payout in candidates:
            if payout.amount > remaining:
                break
            selected.append((payout_type, payout))
            remaining -= payout.amount
    else:
        candidate_by_key = {(payout_type, payout.id): (payout_type, payout) for payout_type, payout in candidates}
        selected_keys = [(item['payout_type'], item['id']) for item in selected_payouts]
        if len(selected_keys) != len(set(selected_keys)):
            raise exceptions.ValidationError({'selected_payouts': 'A payout cannot be selected more than once.'})
        missing_keys = [key for key in selected_keys if key not in candidate_by_key]
        if missing_keys:
            raise exceptions.ValidationError({'selected_payouts': 'Selected payout is unavailable or already paid.'})
        selected = [candidate_by_key[key] for key in selected_keys]
        selected_amount = sum((payout.amount for _, payout in selected), Decimal('0.00'))
        if selected_amount > amount:
            raise exceptions.ValidationError({'selected_payouts': 'Selected payouts exceed the payment amount.'})
        remaining = amount - selected_amount

    return {
        'payouts': selected,
        'candidates': candidates,
        'allocated_amount': amount - remaining,
        'advance_amount': remaining,
    }


def preview_teacher_payment(*, user, teacher_id, amount, selected_payouts=None):
    ensure_finance_admin(user, 'allocate teacher payments')
    candidates = _teacher_payout_candidates(teacher_id)
    return _build_teacher_payment_allocation(
        amount=amount,
        candidates=candidates,
        selected_payouts=selected_payouts,
    )


def _payment_timestamp(paid_at):
    if paid_at is None:
        return timezone.now()
    if isinstance(paid_at, datetime):
        return timezone.make_aware(paid_at) if timezone.is_naive(paid_at) else paid_at
    return timezone.make_aware(datetime.combine(paid_at, time.min))


@transaction.atomic
def allocate_teacher_payment(*, user, teacher_id, amount, paid_at=None, comment='', selected_payouts=None):
    ensure_finance_admin(user, 'allocate teacher payments')
    candidates = _teacher_payout_candidates(teacher_id, for_update=True)
    allocation = _build_teacher_payment_allocation(
        amount=amount,
        candidates=candidates,
        selected_payouts=selected_payouts,
    )
    payment_timestamp = _payment_timestamp(paid_at)

    for payout_type, payout in allocation['payouts']:
        payout.status = PayoutStatus.PAID
        payout.paid_at = payment_timestamp
        update_fields = ['status', 'paid_at']
        if payout.approved_at is None:
            payout.approved_at = payment_timestamp
            update_fields.append('approved_at')
        payout.save(update_fields=update_fields)

    references = [f'{payout_type}:{payout.id}' for payout_type, payout in allocation['payouts']]
    comment_parts = [comment.strip()] if comment and comment.strip() else []
    if references:
        comment_parts.append(f"Рахунки: {', '.join(references)}")
    if allocation['advance_amount']:
        comment_parts.append(f"Аванс: {allocation['advance_amount']:.2f}")

    payment = TeacherPayment.objects.create(
        teacher_id=teacher_id,
        amount=amount,
        paid_at=payment_timestamp.date(),
        comment='; '.join(comment_parts),
        created_by=user,
    )
    return payment, allocation

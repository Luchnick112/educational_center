from decimal import Decimal

from django.db import migrations


BILLING_LESSON_COUNT = 10


def recalculate_draft_financial_documents(apps, schema_editor):
    GroupPricing = apps.get_model('academics', 'GroupPricing')
    Lesson = apps.get_model('academics', 'Lesson')
    LessonParticipant = apps.get_model('academics', 'LessonParticipant')
    ParentCharge = apps.get_model('finance', 'ParentCharge')
    TeacherPayout = apps.get_model('finance', 'TeacherPayout')

    participants = LessonParticipant.objects.select_related(
        'lesson__group',
        'enrollment__student',
    ).filter(
        lesson__status='completed',
    )
    for participant in participants.iterator():
        lesson = participant.lesson
        pricing = (
            GroupPricing.objects.filter(
                group_id=lesson.group_id,
                effective_from__lte=lesson.starts_at,
            )
            .order_by('-effective_from', '-id')
            .values_list('student_price', 'teacher_rate')
            .first()
        )
        student_price = pricing[0] if pricing else lesson.group.student_price
        teacher_rate = pricing[1] if pricing else lesson.group.teacher_rate

        if participant.enrollment.student_price_override is not None:
            billed_amount = participant.enrollment.student_price_override
        elif participant.enrollment.student.lesson_price is not None:
            billed_amount = participant.enrollment.student.lesson_price
        else:
            billed_amount = student_price

        if participant.billed_amount != billed_amount:
            LessonParticipant.objects.filter(pk=participant.pk).update(billed_amount=billed_amount)

        if lesson.group.format == 'individual':
            if participant.attendance_status == 'present':
                payroll_amount = participant.enrollment.teacher_rate_override or teacher_rate
            else:
                payroll_amount = Decimal('0.00')
            if participant.payroll_amount != payroll_amount:
                LessonParticipant.objects.filter(pk=participant.pk).update(payroll_amount=payroll_amount)

    draft_charges = ParentCharge.objects.filter(status='draft').select_related(
        'participant__lesson',
    )
    for charge in draft_charges.iterator():
        if charge.lesson_count == 1:
            amount = charge.participant.billed_amount
        else:
            batch_start = (charge.billing_period - 1) * BILLING_LESSON_COUNT
            lesson_ids = list(
                Lesson.objects.filter(
                    group_id=charge.participant.lesson.group_id,
                    status='completed',
                )
                .order_by('completed_at', 'id')
                .values_list('id', flat=True)[batch_start:batch_start + BILLING_LESSON_COUNT]
            )
            amount = sum(
                LessonParticipant.objects.filter(
                    lesson_id__in=lesson_ids,
                    student_id=charge.student_id,
                ).values_list('billed_amount', flat=True),
                Decimal('0.00'),
            )
        if charge.amount != amount:
            ParentCharge.objects.filter(pk=charge.pk).update(amount=amount)

    draft_payouts = TeacherPayout.objects.filter(
        status='draft',
        participant__lesson__status='completed',
        participant__lesson__group__format='individual',
    ).select_related('participant')
    for payout in draft_payouts.iterator():
        participant = payout.participant
        amount = (
            participant.payroll_amount
            if participant.attendance_status == 'present'
            else Decimal('0.00')
        )
        if payout.amount != amount:
            TeacherPayout.objects.filter(pk=payout.pk).update(amount=amount)


class Migration(migrations.Migration):
    dependencies = [
        ('academics', '0015_lesson_teacher'),
        ('finance', '0005_billing_period_fields'),
    ]

    operations = [
        migrations.RunPython(recalculate_draft_financial_documents, migrations.RunPython.noop),
    ]

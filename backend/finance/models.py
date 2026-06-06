from django.db import models

from academics.models import LessonParticipant
from users.models import ParentProfile, StudentProfile, TeacherProfile, User


class ChargeStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ISSUED = 'issued', 'Issued'
    PAID = 'paid', 'Paid'
    CANCELLED = 'cancelled', 'Cancelled'


class PayoutStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    APPROVED = 'approved', 'Approved'
    PAID = 'paid', 'Paid'
    CANCELLED = 'cancelled', 'Cancelled'


class ParentCharge(models.Model):
    participant = models.OneToOneField(LessonParticipant, on_delete=models.CASCADE, related_name='parent_charge')
    parent = models.ForeignKey(ParentProfile, on_delete=models.PROTECT, related_name='charges')
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='charges')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=ChargeStatus.choices, default=ChargeStatus.DRAFT)
    due_date = models.DateField(null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.parent} / {self.amount}'


class TeacherPayout(models.Model):
    participant = models.OneToOneField(LessonParticipant, on_delete=models.CASCADE, related_name='teacher_payout')
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=PayoutStatus.choices, default=PayoutStatus.DRAFT)
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.teacher} / {self.amount}'


class StudentPayment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_payments_created')

    def __str__(self) -> str:
        return f'{self.student} / {self.amount} / {self.paid_at}'


class TeacherPayment(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_payments_created')

    def __str__(self) -> str:
        return f'{self.teacher} / {self.amount} / {self.paid_at}'

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    TEACHER = 'teacher', 'Teacher'
    PARENT = 'parent', 'Parent'
    STUDENT = 'student', 'Student'


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    phone = models.CharField(max_length=32, blank=True)
    # Telegram usernames are 5-32 chars, letters/numbers/underscore. We keep it nullable to avoid
    # breaking existing fixtures/data; registration flow enforces it as required.
    # Store in canonical "@username" form (so max length is 33).
    telegram_username = models.CharField(max_length=33, unique=True, null=True, blank=True)
    telegram_chat_id = models.BigIntegerField(unique=True, null=True, blank=True)
    telegram_user_id = models.BigIntegerField(unique=True, null=True, blank=True)

    def __str__(self) -> str:
        identity = self.get_full_name() or self.telegram_username or self.username or self.email
        return f'{identity} ({self.role})'


class TelegramLinkToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='telegram_link_tokens')
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: store the linking result for audit/debug.
    linked_chat_id = models.BigIntegerField(null=True, blank=True)
    linked_user_id = models.BigIntegerField(null=True, blank=True)
    linked_username = models.CharField(max_length=64, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]

    def is_active(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()

    def __str__(self) -> str:
        status = 'used' if self.used_at else ('active' if self.expires_at > timezone.now() else 'expired')
        return f'TelegramLinkToken(user_id={self.user_id}, status={status})'


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    grade = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)

    def clean(self) -> None:
        if self.user.role != UserRole.STUDENT:
            raise ValidationError('Student profile can only be linked to a student user.')

    def __str__(self) -> str:
        return str(self.user)


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    billing_notes = models.TextField(blank=True)

    def clean(self) -> None:
        if self.user.role != UserRole.PARENT:
            raise ValidationError('Parent profile can only be linked to a parent user.')

    def __str__(self) -> str:
        return str(self.user)


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bio = models.TextField(blank=True)

    def clean(self) -> None:
        if self.user.role != UserRole.TEACHER:
            raise ValidationError('Teacher profile can only be linked to a teacher user.')

    def __str__(self) -> str:
        return str(self.user)


class StudentParentRelation(models.Model):
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='student_links')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='parent_links')
    is_primary = models.BooleanField(default=False)
    is_financial_contact = models.BooleanField(default=True)

    class Meta:
        unique_together = ('parent', 'student')

    def __str__(self) -> str:
        return f'{self.parent} -> {self.student}'

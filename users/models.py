from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    TEACHER = 'teacher', 'Teacher'
    PARENT = 'parent', 'Parent'
    STUDENT = 'student', 'Student'


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    phone = models.CharField(max_length=32, blank=True)

    def __str__(self) -> str:
        return f'{self.get_full_name() or self.email or self.username} ({self.role})'


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
    relationship = models.CharField(max_length=64, blank=True)
    is_primary = models.BooleanField(default=False)
    is_financial_contact = models.BooleanField(default=True)

    class Meta:
        unique_together = ('parent', 'student')

    def __str__(self) -> str:
        return f'{self.parent} -> {self.student}'

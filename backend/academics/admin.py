from django.contrib import admin

from .models import (
    GroupPricing,
    Lesson,
    LessonConfirmation,
    LessonParticipant,
    LessonRescheduleRequest,
    StudentEnrollment,
    StudyGroup,
    Subject,
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'teacher', 'capacity', 'is_active')
    list_filter = ('is_active', 'subject')
    search_fields = ('name', 'subject__name', 'teacher__user__first_name', 'teacher__user__last_name')


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'status', 'start_date', 'end_date')
    list_filter = ('status',)


class LessonParticipantInline(admin.TabularInline):
    model = LessonParticipant
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('id', 'group', 'starts_at', 'status')
    list_filter = ('status', 'group__subject')
    inlines = (LessonParticipantInline,)


@admin.register(LessonConfirmation)
class LessonConfirmationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'requested_from', 'status', 'confirmer', 'confirmed_at')
    list_filter = ('requested_from', 'status')


@admin.register(LessonRescheduleRequest)
class LessonRescheduleRequestAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'student', 'status', 'requested_starts_at', 'parent_confirmed_at', 'applied_at')
    list_filter = ('status',)
    search_fields = ('student__user__first_name', 'student__user__last_name', 'lesson__group__name')


@admin.register(GroupPricing)
class GroupPricingAdmin(admin.ModelAdmin):
    list_display = ('group', 'effective_from', 'student_price', 'teacher_rate', 'created_at')
    list_filter = ('group',)
    search_fields = ('group__name',)

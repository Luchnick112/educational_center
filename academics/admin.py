from django.contrib import admin

from .models import Lesson, LessonConfirmation, LessonParticipant, StudentEnrollment, StudyGroup, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'teacher', 'format', 'capacity', 'is_active')
    list_filter = ('format', 'is_active', 'subject')
    search_fields = ('name', 'subject__name', 'teacher__user__first_name', 'teacher__user__last_name')


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'group__format')


class LessonParticipantInline(admin.TabularInline):
    model = LessonParticipant
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'starts_at', 'ends_at', 'status')
    list_filter = ('status', 'group__format', 'group__subject')
    inlines = (LessonParticipantInline,)


@admin.register(LessonConfirmation)
class LessonConfirmationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'requested_from', 'status', 'confirmer', 'confirmed_at')
    list_filter = ('requested_from', 'status')

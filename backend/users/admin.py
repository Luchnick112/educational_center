from django.contrib import admin

from .models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, TelegramLinkToken, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_username', 'telegram_chat_id', 'email', 'username', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('telegram_username', 'email', 'username', 'first_name', 'last_name')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson_price')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'hourly_rate')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(StudentParentRelation)
class StudentParentRelationAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'is_primary', 'is_financial_contact')
    list_filter = ('is_primary', 'is_financial_contact')


@admin.register(TelegramLinkToken)
class TelegramLinkTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'expires_at', 'used_at', 'linked_chat_id', 'linked_user_id')
    search_fields = ('user__username', 'user__telegram_username', 'token')
    list_filter = ('used_at',)

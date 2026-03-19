from django.contrib import admin

from .models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'grade', 'date_of_birth')
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
    list_display = ('parent', 'student', 'relationship', 'is_primary', 'is_financial_contact')
    list_filter = ('is_primary', 'is_financial_contact')

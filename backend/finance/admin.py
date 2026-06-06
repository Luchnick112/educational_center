from django.contrib import admin

from .models import ParentCharge, StudentPayment, TeacherPayment, TeacherPayout


@admin.register(ParentCharge)
class ParentChargeAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'amount', 'status', 'due_date', 'paid_at')
    list_filter = ('status',)


@admin.register(TeacherPayout)
class TeacherPayoutAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'amount', 'status', 'approved_at', 'paid_at')
    list_filter = ('status',)


@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'paid_at', 'created_by', 'created_at')
    list_filter = ('paid_at',)
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__user__telegram_username')


@admin.register(TeacherPayment)
class TeacherPaymentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'amount', 'paid_at', 'created_by', 'created_at')
    list_filter = ('paid_at',)
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name', 'teacher__user__telegram_username')

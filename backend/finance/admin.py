from django.contrib import admin

from .models import ParentCharge, TeacherPayout


@admin.register(ParentCharge)
class ParentChargeAdmin(admin.ModelAdmin):
    list_display = ('parent', 'student', 'amount', 'status', 'due_date', 'paid_at')
    list_filter = ('status',)


@admin.register(TeacherPayout)
class TeacherPayoutAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'amount', 'status', 'approved_at', 'paid_at')
    list_filter = ('status',)

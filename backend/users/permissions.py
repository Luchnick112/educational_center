from rest_framework import permissions

from .models import UserRole


class StaffWritePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        # "admin" role should have the same write privileges as Django staff in the API.
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.role == UserRole.ADMIN)
        )


class StaffOrTeacherWritePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_staff
                or request.user.role in {UserRole.ADMIN, UserRole.TEACHER}
            )
        )


class IsAdminUserRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.role == UserRole.ADMIN)
        )


class IsAdminOrRelatedAcademicObject(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.role == UserRole.ADMIN:
            return True

        if hasattr(obj, 'group') and hasattr(obj.group, 'teacher_id'):
            if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
                return obj.group.teacher_id == user.teacher_profile.id
            if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
                return obj.participants.filter(student=user.student_profile).exists()
            if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
                return obj.participants.filter(student__parent_links__parent=user.parent_profile).exists()

        if hasattr(obj, 'teacher_id') and hasattr(obj, 'enrollments'):
            if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
                return obj.teacher_id == user.teacher_profile.id
            if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
                return obj.enrollments.filter(student=user.student_profile).exists()
            if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
                return obj.enrollments.filter(student__parent_links__parent=user.parent_profile).exists()

        if hasattr(obj, 'student_id'):
            if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
                return obj.student_id == user.student_profile.id
            if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
                return obj.student.parent_links.filter(parent=user.parent_profile).exists()
            if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
                return obj.group.teacher_id == user.teacher_profile.id

        if hasattr(obj, 'participant_id'):
            participant = obj.participant
            if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
                return participant.student_id == user.student_profile.id
            if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
                return participant.student.parent_links.filter(parent=user.parent_profile).exists()
            if user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile'):
                return participant.lesson.group.teacher_id == user.teacher_profile.id

        if hasattr(obj, 'teacher_id'):
            return user.role == UserRole.TEACHER and hasattr(user, 'teacher_profile') and obj.teacher_id == user.teacher_profile.id

        if hasattr(obj, 'parent_id'):
            if user.role == UserRole.PARENT and hasattr(user, 'parent_profile'):
                return obj.parent_id == user.parent_profile.id
            if user.role == UserRole.STUDENT and hasattr(user, 'student_profile'):
                return obj.student_id == user.student_profile.id

        return False

from rest_framework.routers import DefaultRouter

from .api import (
    GroupPricingViewSet,
    LessonConfirmationViewSet,
    LessonRescheduleRequestViewSet,
    LessonViewSet,
    StudentEnrollmentViewSet,
    StudyGroupViewSet,
    SubjectViewSet,
)

router = DefaultRouter()
router.register('subjects', SubjectViewSet, basename='subject')
router.register('groups', StudyGroupViewSet, basename='group')
router.register('group-pricings', GroupPricingViewSet, basename='group-pricing')
router.register('enrollments', StudentEnrollmentViewSet, basename='enrollment')
router.register('lessons', LessonViewSet, basename='lesson')
router.register('confirmations', LessonConfirmationViewSet, basename='confirmation')
router.register('reschedule-requests', LessonRescheduleRequestViewSet, basename='reschedule-request')

urlpatterns = router.urls

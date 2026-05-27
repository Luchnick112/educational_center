from rest_framework.routers import DefaultRouter

from .api import ParentChargeViewSet, StudentPaymentViewSet, TeacherPaymentViewSet, TeacherPayoutViewSet

router = DefaultRouter()
router.register('parent-charges', ParentChargeViewSet, basename='parent-charge')
router.register('teacher-payouts', TeacherPayoutViewSet, basename='teacher-payout')
router.register('student-payments', StudentPaymentViewSet, basename='student-payment')
router.register('teacher-payments', TeacherPaymentViewSet, basename='teacher-payment')

urlpatterns = router.urls

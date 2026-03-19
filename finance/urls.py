from rest_framework.routers import DefaultRouter

from .api import ParentChargeViewSet, TeacherPayoutViewSet

router = DefaultRouter()
router.register('parent-charges', ParentChargeViewSet, basename='parent-charge')
router.register('teacher-payouts', TeacherPayoutViewSet, basename='teacher-payout')

urlpatterns = router.urls

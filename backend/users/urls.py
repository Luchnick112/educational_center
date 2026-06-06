from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import (
    ParentProfileViewSet,
    RegisterView,
    StudentProfileViewSet,
    StudentParentRelationViewSet,
    TeacherProfileViewSet,
    TelegramLinkTokenView,
    TelegramWebhookView,
    TokenPageView,
    TokenRefreshPageView,
    UserViewSet,
)

router = DefaultRouter()
router.register('', UserViewSet, basename='user')
router.register('students', StudentProfileViewSet, basename='student')
router.register('parents', ParentProfileViewSet, basename='parent')
router.register('student-parent-relations', StudentParentRelationViewSet, basename='student-parent-relation')
router.register('teachers', TeacherProfileViewSet, basename='teacher')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenPageView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshPageView.as_view(), name='token_refresh'),
    path('telegram/link-token/', TelegramLinkTokenView.as_view(), name='telegram-link-token'),
    path('telegram/webhook/', TelegramWebhookView.as_view(), name='telegram-webhook'),
]

urlpatterns += router.urls

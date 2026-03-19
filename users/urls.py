from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import (
    ParentProfileViewSet,
    RegisterView,
    StudentProfileViewSet,
    TeacherProfileViewSet,
    TokenPageView,
    TokenRefreshPageView,
    UserViewSet,
)

router = DefaultRouter()
router.register('', UserViewSet, basename='user')
router.register('students', StudentProfileViewSet, basename='student')
router.register('parents', ParentProfileViewSet, basename='parent')
router.register('teachers', TeacherProfileViewSet, basename='teacher')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenPageView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshPageView.as_view(), name='token_refresh'),
]

urlpatterns += router.urls

from django.urls import path

from .views import (
    MyChildrenSummaryView,
    MyChildrenView,
    MyConfirmationsView,
    MyLessonsView,
    MyNotificationsView,
    MyPaymentsView,
)

urlpatterns = [
    path('lessons/', MyLessonsView.as_view(), name='lessons'),
    path('children/', MyChildrenView.as_view(), name='children'),
    path('children-summary/', MyChildrenSummaryView.as_view(), name='children-summary'),
    path('payments/', MyPaymentsView.as_view(), name='payments'),
    path('confirmations/', MyConfirmationsView.as_view(), name='confirmations'),
    path('notifications/', MyNotificationsView.as_view(), name='notifications'),
]

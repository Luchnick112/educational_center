from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import MeView, MyChildrenSummaryView, MyChildrenView, MyConfirmationsView, MyLessonsView, MyPaymentsView

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('users/', include('users.urls')),
    path('academics/', include('academics.urls')),
    path('finance/', include('finance.urls')),
    path('me/', MeView.as_view(), name='me'),
    path('my-lessons/', MyLessonsView.as_view(), name='my-lessons'),
    path('my-children/', MyChildrenView.as_view(), name='my-children'),
    path('my-children-summary/', MyChildrenSummaryView.as_view(), name='my-children-summary'),
    path('my-payments/', MyPaymentsView.as_view(), name='my-payments'),
    path('my-confirmations/', MyConfirmationsView.as_view(), name='my-confirmations'),
]

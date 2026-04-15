from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import MeView

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('users/', include('users.urls')),
    path('academics/', include('academics.urls')),
    path('finance/', include('finance.urls')),
    path('me/', MeView.as_view(), name='me'),

    # "My" namespace: personal resources for the currently authenticated user.
    path('my/', include(('core.my_urls', 'my'), namespace='my')),
]

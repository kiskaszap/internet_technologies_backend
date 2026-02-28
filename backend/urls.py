from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from marketplace.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT Authentication (custom login)
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Marketplace API
    path("api/", include("marketplace.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

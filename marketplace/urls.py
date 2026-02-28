from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    ListingViewSet,
    CommentViewSet,
    RegisterView,
)

"""
API routing configuration.

Uses DRF DefaultRouter for RESTful resources
and explicit paths for custom authentication flows.
"""

# Router automatically generates REST endpoints:
# GET / POST / PUT / PATCH / DELETE
# Ensures consistent RESTful API structure.

from .views import VerifyOTPView


router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("listings", ListingViewSet)
router.register("comments", CommentViewSet)

urlpatterns = router.urls + [
    # Custom authentication endpoints are defined manually
    # because they do not follow standard CRUD patterns.
    path("register/", RegisterView.as_view(), name="register"),
    # OTP verification separated to enforce two-step account activation
      path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
]

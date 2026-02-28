
from rest_framework import viewsets, permissions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Category, Listing, Comment, EmailOTP
from .serializers import CategorySerializer, ListingSerializer, CommentSerializer

import random


User = get_user_model()




class IsOwnerOrReadOnly(permissions.BasePermission):
    #  """
    # Custom object-level permission.

    # Allows:
    # - Read access for everyone (SAFE_METHODS)
    # - Write access only to the owner of the object

    # Enforces ownership-based security for listings.
    # """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]



    # """
    # Main CRUD controller for listings.

    # Implements:
    # - Public read access
    # - Authenticated creation
    # - Owner-only update/delete
    # - Server-side filtering via query parameter (?my=true)
    # """
class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all().order_by("-created_at")
    serializer_class = ListingSerializer
        # """
        # Enables server-side filtering to reduce data transfer
        # and prevent exposing unnecessary records.
        # """
    def get_queryset(self):
        queryset = Listing.objects.all().order_by("-created_at")

       
        if self.request.query_params.get("my") == "true":
            return queryset.filter(user=self.request.user)

        return queryset
        # """
        # Method-based permission control.

        # - POST requires authentication
        # - PUT/PATCH/DELETE require authentication + ownership
        # - GET allowed for everyone
        # """
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        elif self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return [AllowAny()]
        # """
        # Automatically associates the listing with the logged-in user.
        # Prevents client-side user spoofing.
        # """
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



    # """
    # Handles listing comments.

    # - Public read access
    # - Authenticated comment creation
    # - Server-side filtering by listing ID
    # """
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()   
    serializer_class = CommentSerializer
        # """
        # Supports filtering comments by listing via query parameter.
        # Reduces unnecessary payload size.
        # """
    def get_queryset(self):
        queryset = Comment.objects.all().order_by("-created_at")
        listing_id = self.request.query_params.get("listing")

        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)

        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]
    # """
        # Prevents user injection by assigning request.user server-side.
        # """
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # """
    # Custom registration flow with university email validation
    # and email-based OTP verification.

    # Users are created as inactive until OTP verification succeeds.
    # """
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        raw_email = request.data.get("email")
        password = request.data.get("password")

        if not raw_email or not password:
            return Response(
                {"message": "Email and password required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = raw_email.strip()
        email_lower = email.lower()
        # """
        # Enforces University of Glasgow domain restriction.
        # Prevents non-university account creation.
        # """
        if email_lower.endswith("@student.gla.ac.uk"):
            local_part, _ = email.split("@")

            if local_part and local_part[-1].isalpha():
                local_part = local_part[:-1] + local_part[-1].upper()

            email = f"{local_part}@student.gla.ac.uk"

        elif email_lower.endswith("@glasgow.ac.uk"):
            local_part, _ = email.split("@")
            email = f"{local_part}@glasgow.ac.uk"

        else:
            return Response(
                {"message": "Only University of Glasgow emails are allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

# Prevent duplicate registrations
        if User.objects.filter(username__iexact=email).exists():
            return Response(
                {"message": "This email is already registered"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=email,
            password=password,
            is_active=False,
        )

        # """
        # Generate secure 6-digit OTP.
        # Stored separately to allow expiration control.
        # """
        otp_code = str(random.randint(100000, 999999))

        EmailOTP.objects.create(
            user=user,
            otp=otp_code,
        )
# Email-based verification improves account authenticity
        send_mail(
            "UofG Marketplace Verification Code",
            f"Your verification code is: {otp_code}",
            None,
            [email],
            fail_silently=False,
        )

        return Response(
            {"message": "OTP has been sent to your university email"},
            status=status.HTTP_201_CREATED,
        )

    # """
    # Verifies OTP and activates user account.
    # """

class VerifyOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        raw_email = request.data.get("email")
        otp = request.data.get("otp")

        if not raw_email or not otp:
            return Response(
                {"message": "Email and OTP required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = raw_email.strip()

        try:
            user = User.objects.get(username__iexact=email)
            otp_obj = EmailOTP.objects.filter(user=user).latest("created_at")
        except:
            return Response(
                {"message": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_obj.otp != otp:
            return Response(
                {"message": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp_obj.is_valid():
            return Response(
                {"message": "OTP expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.save()

        otp_obj.delete()  

        return Response(
            {"message": "Account verified successfully"},
            status=status.HTTP_200_OK,
        )


    """
    Extends default JWT login to:
    - Enforce university email validation
    - Normalize email format
    - Block login for unverified users
    """
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        raw_email = attrs.get("username")
        password = attrs.get("password")

        if not raw_email or not password:
            raise AuthenticationFailed("Email and password required")

        email = raw_email.strip()
        email_lower = email.lower()

     # Apply same email normalization rules as registration
        if email_lower.endswith("@student.gla.ac.uk"):
            local_part, _ = email.split("@")
            if local_part and local_part[-1].isalpha():
                local_part = local_part[:-1] + local_part[-1].upper()
            email = f"{local_part}@student.gla.ac.uk"

        elif email_lower.endswith("@glasgow.ac.uk"):
            local_part, _ = email.split("@")
            email = f"{local_part}@glasgow.ac.uk"

        else:
            raise AuthenticationFailed("Invalid university email")

        try:
            user = User.objects.get(username__iexact=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid credentials")

        if not user.is_active:
            raise AuthenticationFailed("Please verify your email first")

        attrs["username"] = user.username

        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

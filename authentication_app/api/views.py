"""
REST API views for authentication flows.

Endpoints covered:
- POST /api/register/         → Create inactive user + send activation email.
- POST /api/activate/         → Activate via JSON payload {uid, token}.
- GET  /api/activate/<uid>/<token>/ → Activate via URL (browser-friendly).
- POST /api/login/            → Issue JWTs (HttpOnly cookies).
- POST /api/logout/           → Blacklist refresh token + clear cookies.
- POST /api/token/refresh/    → Rotate access token (reads refresh cookie).
- POST /api/password_reset/   → Send password reset email (neutral response).
- POST /api/password_confirm/<uid>/<token>/ → Validate token & set new password.

Security highlights:
- Uses DRF SimpleJWT tokens stored in HttpOnly cookies.
- Neutral responses for password reset (do not leak whether an email exists).
- Validations are explicit, with status codes that align to common REST usage.
"""

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from .serializers import RegistrationSerializer
from .email_utils import send_activation_email, send_password_reset_email

class RegistrationView(APIView):
    """
    Create an inactive user and send an activation email.

    Request (JSON):
        {
          "email": "user@example.com",
          "password": "********",
          "confirmed_password": "********"
        }

    Response 201:
        {
          "user": {"id": <int>, "email": "<email>"},
          "detail": "Activation email sent."
        }

    Errors:
        400 - Validation errors (email taken, or password mismatch)
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        send_activation_email(user)

        return Response(
            {
                'user': {'id': user.id, 'email': user.email},
                'detail': 'Activation email sent.'
            },
            status=status.HTTP_201_CREATED,
        )

class ActivateAccountView(APIView):
    """
    Activate a user from a JSON payload (mobile/SPA-friendly).

    Request (JSON):
        {
          "uid": "<base64 user id>",
          "token": "<activation token>"
        }

    Response 200:
        {"detail": "Account activated."}

    Errors:
        400 - Invalid payload, invalid/expired token, or unknown user
    """

    permission_classes = [AllowAny]

    def post(self, request):
        uidb64 = request.data.get("uid")
        token  = request.data.get("token")
        if not uidb64 or not token:
            return Response({"detail": "Invalid payload."}, status=400)
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Invalid token."}, status=400)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"detail": "Account activated."})
        return Response({"detail": "Invalid or expired token."}, status=400)
    
class ActivateAccountLinkView(APIView):
    """
    Activate a user directly via URL parameters (usable from an email link).

    Response 200:
        {"message": "Account successfully activated."}

    Errors:
        400 - Decoding failure, unknown user, invalid/expired token
    """

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save()
            return Response({'message': 'Account successfully activated.'}, status=status.HTTP_200_OK)

        return Response({'message': 'Activation failed.'}, status=status.HTTP_400_BAD_REQUEST)
    
def _set_jwt_cookies(response, refresh_token, access_token):
    """
    Helper to set `access_token` and `refresh_token` as HttpOnly cookies.

    Cookie attributes:
      - `HttpOnly`: True
      - `Secure`: derives from Django's `SESSION_COOKIE_SECURE`
      - `SameSite`: derives from `CSRF_COOKIE_SAMESITE`
      - `Path`: "/"
      - `Max-Age`: taken from SimpleJWT lifetimes

    Note:
      This function mutates and returns the passed Response object.
    """

    from django.conf import settings

    access_max_age  = int(getattr(settings, 'SIMPLE_JWT', {}).get('ACCESS_TOKEN_LIFETIME').total_seconds()) if getattr(settings, 'SIMPLE_JWT', None) else 60*30
    refresh_max_age = int(getattr(settings, 'SIMPLE_JWT', {}).get('REFRESH_TOKEN_LIFETIME').total_seconds()) if getattr(settings, 'SIMPLE_JWT', None) else 60*60*24*7

    secure   = getattr(settings, 'SESSION_COOKIE_SECURE', False)
    samesite = getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax')

    response.set_cookie(
        key='access_token',
        value=str(access_token),
        max_age=access_max_age,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
    
    response.set_cookie(
        key='refresh_token',
        value=str(refresh_token),
        max_age=refresh_max_age,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
    return response

class LoginView(APIView):
    """
    Authenticate a user by email+password and set JWT cookies.

    Request (JSON):
        {"email": "<email>", "password": "<password>"}

    Response 200:
        {
          "detail": "Login successful",
          "user": {"id": <int>, "username": "<email>"}
        }
        (Sets `access_token` and `refresh_token` cookies.)

    Errors:
        400 - Missing credentials
        401 - Invalid credentials / inactive account
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or "").strip().lower()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if user is None:
            try:
                u = User.objects.get(email=email)
                if not u.is_active:
                    return Response({'detail': 'No active account found with the given credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                pass
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access  = refresh.access_token

        resp = Response(
            {
                'detail': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                },
            },
            status=status.HTTP_200_OK,
        )
        return _set_jwt_cookies(resp, refresh, access)
    
class LogoutView(APIView):
    """
    Logout by blacklisting the refresh token and clearing cookies.

    Request: (no body)
      Requires the `refresh_token` cookie to be present.

    Response 200:
        {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."}

    Errors:
        400 - Missing or invalid refresh token
    """

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_400_BAD_REQUEST)

        resp = Response(
            {'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'},
            status=status.HTTP_200_OK,
        )
        
        resp.delete_cookie('access_token', path='/')
        resp.delete_cookie('refresh_token', path='/')
        return resp
    
def _set_access_cookie(response, access_token):
    """
    Helper to set only the `access_token` cookie (used by refresh).

    See `_set_jwt_cookies` for cookie attributes and rationale.
    """

    from django.conf import settings
    
    access_max_age = 60 * 30
    if getattr(settings, 'SIMPLE_JWT', None):
        access_max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())

    secure   = getattr(settings, 'SESSION_COOKIE_SECURE', False)
    samesite = getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Lax')

    response.set_cookie(
        key='access_token',
        value=str(access_token),
        max_age=access_max_age,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path='/',
    )
    return response

class CookieTokenRefreshView(APIView):
    """
    Issue a new access token based on the `refresh_token` cookie.

    Request: (no body)
      Reads the refresh token from the `refresh_token` cookie.

    Response 200:
        {"detail": "Token refreshed", "access": "<jwt-string>"}
        (Also sets a fresh `access_token` cookie.)

    Errors:
        400 - Missing refresh cookie
        401 - Invalid refresh token (expired/blacklisted)
    """

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_cookie = request.COOKIES.get('refresh_token')
        if not refresh_cookie:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TokenRefreshSerializer(data={'refresh': refresh_cookie})
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError):
            return Response({'detail': 'Invalid refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        new_access = serializer.validated_data['access']

        resp = Response({'detail': 'Token refreshed', 'access': new_access}, status=status.HTTP_200_OK)
        return _set_access_cookie(resp, new_access)
    
class PasswordResetRequestView(APIView):
    """
    Start the password reset flow by sending a reset email if the user exists.

    Request (JSON):
        {"email": "<email>"}

    Response 200:
        {"detail": "An email has been sent to reset your password."}
        (Always returned, even if the email does not exist, to avoid user enumeration.)

    Errors:
        400 - Missing email field
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'email': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'An email has been sent to reset your password.'}, status=status.HTTP_200_OK)

        send_password_reset_email(user)

        return Response({'detail': 'An email has been sent to reset your password.'}, status=status.HTTP_200_OK)
    
class PasswordResetConfirmLinkView(APIView):
    """
    Confirm and apply a new password using URL-embedded uid/token.

    Request (JSON):
        {
          "new_password": "<new>",
          "confirm_password": "<new>"
        }

    Response 200:
        {"detail": "Your Password has been successfully reset."}

    Errors:
        400 - Invalid payload, token invalid/expired, mismatching passwords,
              or password failing Django's validators.
    """

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not new_password or not confirm_password:
            return Response({'detail': 'Invalid payload.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'new_password': ['Passwords do not match.']}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response({'new_password': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Your Password has been successfully reset.'}, status=status.HTTP_200_OK)
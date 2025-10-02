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
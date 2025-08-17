from django.urls import path
from .views import (
    RegistrationView,
    ActivateAccountView,
    ActivateAccountLinkView,
    LoginView,
    LogoutView,
    CookieTokenRefreshView,
    PasswordResetRequestView,    
    PasswordResetConfirmLinkView
)

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='api-register'),
    path('activate/', ActivateAccountView.as_view(), name='api-activate'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountLinkView.as_view(), name='api-activate-link'),
    path('login/', LoginView.as_view(), name='api-login'),
    path('logout/', LogoutView.as_view(), name='api-logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmLinkView.as_view(), name='password-confirm-link'),
]
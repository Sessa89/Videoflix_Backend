from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.html import format_html

# Register your models here.

@admin.action(description='Activate selected users')
def activate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} user(s) activated.")

@admin.action(description='Resend activation email (only inactive)')
def resend_activation_email(modeladmin, request, queryset):
    base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5500')
    count = 0
    for user in queryset.filter(is_active=False):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        activation_link = f"{base}/activate.html?uid={uidb64}&token={token}"
        send_mail(
            subject='Activate your Videoflix account',
            message=f"Click to activate: {activation_link}",
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[user.email],
            fail_silently=True,
        )
        count += 1
    modeladmin.message_user(request, f"Sent {count} activation email(s).")

class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'is_staff', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    actions = [activate_users, resend_activation_email]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

try:
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

    @admin.register(OutstandingToken)
    class OutstandingTokenAdmin(admin.ModelAdmin):
        list_display = ('jti', 'user', 'created_at', 'expires_at')
        list_filter = ('user',)
        search_fields = ('jti', 'user__email', 'user__username')

    @admin.register(BlacklistedToken)
    class BlacklistedTokenAdmin(admin.ModelAdmin):
        list_display = ('token', 'blacklisted_at')
        search_fields = ('token__jti',)
except Exception:
    pass
"""
Email utilities for activation and password reset flows.

This module centralizes:
- Creation of activation/reset URLs that the frontend understands.
- Rendering of HTML email templates with a plaintext alternative.
- Sending emails via Django's configured email backend.

All functions are intentionally slim to stay reusable inside views and admin.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

def _brand_context():
    base = getattr(settings, "FRONTEND_BASE_URL", "http://127.0.0.1:5500")
    logo_url = f"{base}/assets/icons/logo_icon.svg"
    
    return {
        "brand_name": "Videoflix",
        "brand_logo": logo_url,
        "brand_logo_url": logo_url
    }

def _send_html_email(*, subject: str, template: str, context: dict, to_email: str):
    """
    Render an HTML email from a Django template and send it with a plaintext
    fallback (multipart/alternative).

    Args:
        subject: Subject line of the email.
        template: Template path, e.g. "emails/activation_email.html".
        context: Template context; should include human-friendly strings/URLs.
        to_email: Recipient address.

    Notes:
        - Uses `DEFAULT_FROM_EMAIL` as sender.
        - `fail_silently=True` is intentional for background-friendly behavior.
          Handle delivery monitoring via logs/metrics in production.
    """

    ctx = {**_brand_context(), **context}
    html = render_to_string(template, ctx)
    text = strip_tags(html)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[to_email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)

def build_activation_link(user):
    """
    Build a frontend-facing activation URL for a user.

    The URL encodes the user's id (`uid`) and a one-time token (`token`)
    that the frontend can pass back to the backend to activate the account.

    Returns:
        A full URL (string), e.g. "http://localhost:5500/activate.html?uid=...&token=..."
    """

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    base = getattr(settings, "FRONTEND_BASE_URL", "http://127.0.0.1:5500")
    path = getattr(settings, "FRONTEND_ACTIVATE_PATH", "/pages/auth/activate.html")
    return f"{base.rstrip('/')}{path}?uid={uidb64}&token={token}"

def build_reset_link(user):
    """
    Build a frontend-facing reset URL for a user.

    Returns:
        A full URL (string), e.g. "http://localhost:5500/reset.html?uid=...&token=..."
    """

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    base = getattr(settings, "FRONTEND_BASE_URL", "http://127.0.0.1:5500")
    path = getattr(settings, "FRONTEND_RESET_PATH", "/pages/auth/confirm_password.html")
    return f"{base.rstrip('/')}{path}?uid={uidb64}&token={token}"

def send_activation_email(user):
    """
    Send the activation email to a newly registered (inactive) user.

    Returns:
        The activation URL (string) for logging/debugging if needed.
    """

    activation_url = build_activation_link(user)
    ctx = {
        "subject": "Confirm your email",
        "user_email": user.email,
        "activation_url": activation_url,
    }
    _send_html_email(
        subject=ctx["subject"],
        template="emails/activation_email.html",
        context=ctx,
        to_email=user.email,
    )

    return activation_url

def send_password_reset_email(user):
    """
    Send the password reset email containing a tokenized URL.

    Returns:
        The reset URL (string) for logging/debugging if needed.
    """

    reset_url = build_reset_link(user)
    ctx = {
        "subject": "Reset your Password",
        "user_email": user.email,
        "reset_url": reset_url,
    }
    _send_html_email(
        subject=ctx["subject"],
        template="emails/reset_password_email.html",
        context=ctx,
        to_email=user.email,
    )
    
    return reset_url
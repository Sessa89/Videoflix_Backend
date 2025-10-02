from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

def _send_html_email(*, subject: str, template: str, context: dict, to_email: str):
    html = render_to_string(template, context)
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
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5500")

    return f"{base}/activate.html?uid={uidb64}&token={token}"

def build_reset_link(user):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5500")

    return f"{base}/reset.html?uid={uidb64}&token={token}"

def send_activation_email(user):
    activation_url = build_activation_link(user)
    ctx = {
        "subject": "Activate your Videoflix account",
        "brand_name": "Videoflix",
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
    reset_url = build_reset_link(user)
    ctx = {
        "subject": "Reset your Videoflix password",
        "brand_name": "Videoflix",
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
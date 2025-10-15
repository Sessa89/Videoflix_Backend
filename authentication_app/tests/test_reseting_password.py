"""
Tests for password reset request endpoint.

Covers:
- Known email → success message + email is sent (HTML + text).
- Unknown email → same neutral success message, no email sent.
- Missing email → 400 with field error.
"""

from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

class PasswordResetEndpointTests(APITestCase):
    """
    E2E tests for /api/password_reset/
    """

    def setUp(self):
        self.url = reverse('password-reset')
        self.email = 'pwreset@example.com'
        User.objects.create_user(username=self.email, email=self.email, password='secret123', is_active=True)

    def test_password_reset_sends_email_and_returns_200(self):
        """
        Happy path: a reset email with HTML alternative is sent.
        """

        resp = self.client.post(self.url, {'email': self.email}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('detail'), 'An email has been sent to reset your password.')
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.email, mail.outbox[0].to)
        self.assertIn('Reset', mail.outbox[0].subject)

    def test_password_reset_unknown_email_still_returns_200_no_mail(self):
        """
        Neutral response: unknown email still returns 200, but no email is sent.
        """

        resp = self.client.post(self.url, {'email': 'unknown@example.com'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('detail'), 'An email has been sent to reset your password.')
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_missing_email_returns_400(self):
        """
        Missing `email` field yields 400 with field error.
        """

        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', resp.data)

    def test_password_reset_sends_html_email(self):
        """
        Ensure a multipart/alternative email is generated (HTML body present).
        """

        resp = self.client.post(self.url, {'email': self.email}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        
        self.assertTrue(hasattr(msg, "alternatives"))
        self.assertGreaterEqual(len(msg.alternatives), 1)
        content, mimetype = msg.alternatives[0]
        self.assertEqual(mimetype, "text/html")
        self.assertIn("Reset password", content)
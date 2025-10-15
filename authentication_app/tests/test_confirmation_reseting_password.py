"""
Tests for password reset confirmation endpoint.

Covers:
- Happy path: set a new password and login with it.
- Invalid token → 400.
- Password mismatch → 400 with field error.
- Weak password → 400 from Django validators.
"""

from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase


class PasswordResetConfirmLinkTests(APITestCase):
    """
    E2E tests for /api/password_confirm/<uidb64>/<token>/
    """

    def setUp(self):
        self.login_url = reverse('api-login')
        self.email = 'linkconfirm@test.com'
        self.old_pw = 'oldPassword123!'
        self.user = User.objects.create_user(
            username=self.email, email=self.email, password=self.old_pw, is_active=True
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def _url(self, uid=None, token=None):
        """
        Helper: build the confirm URL with uid/token path params.
        """

        return reverse('password-confirm-link', kwargs={
            'uidb64': uid or self.uidb64,
            'token': token or self.token
        })

    def test_success_resets_password_and_allows_login_with_new_password(self):
        """
        End-to-end: reset password and ensure login works only with the new password.
        """

        new_pw = 'NewPassword123!'
        resp = self.client.post(self._url(), {
            'new_password': new_pw,
            'confirm_password': new_pw,
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('detail'), 'Your Password has been successfully reset.')

        bad = self.client.post(self.login_url, {'email': self.email, 'password': self.old_pw}, format='json')
        self.assertEqual(bad.status_code, status.HTTP_401_UNAUTHORIZED)

        ok = self.client.post(self.login_url, {'email': self.email, 'password': new_pw}, format='json')
        self.assertEqual(ok.status_code, status.HTTP_200_OK)

    def test_invalid_token_returns_400(self):
        """
        Forged/expired token should be rejected.
        """

        resp = self.client.post(self._url(token='invalid'), {
            'new_password': 'SomePassword123!',
            'confirm_password': 'SomePassword123!',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid', resp.data.get('detail', ''))

    def test_password_mismatch_returns_400(self):
        """
        Both passwords must match.
        """

        resp = self.client.post(self._url(), {
            'new_password': 'Aaa12345!',
            'confirm_password': 'Different123!',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Passwords do not match', resp.data.get('new_password', [])[0])

    def test_weak_password_returns_400(self):
        """
        Weak passwords fail Django's built-in validators.
        """

        resp = self.client.post(self._url(), {
            'new_password': '123',
            'confirm_password': '123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', resp.data)
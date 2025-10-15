"""
Tests for login endpoint.

Covers:
- Login fails before activation.
- Login succeeds after activation and sets cookies.
- Wrong password and missing fields return appropriate error codes.
"""

from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase


class LoginEndpointTests(APITestCase):
    """
    E2E tests for /api/login/
    """

    def setUp(self):
        self.register_url = reverse('api-register')
        self.activate_url = reverse('api-activate')
        self.login_url = reverse('api-login')

        self.email = 'loginuser@example.com'
        self.password = 'securepassword'

        reg = self.client.post(
            self.register_url,
            {
                'email': self.email,
                'password': self.password,
                'confirmed_password': self.password,
            },
            format='json',
        )
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)

        self.user = User.objects.get(email=self.email)
        self.token = reg.data['token']
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

    def _activate(self):
        """
        Helper: activate the freshly created user.
        """

        resp = self.client.post(self.activate_url, {'uid': self.uidb64, 'token': self.token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_login_fails_before_activation(self):
        """
        Inactive users cannot log in.
        """

        resp = self.client.post(self.login_url, {'email': self.email, 'password': self.password}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
    
        self.assertIn('detail', resp.data)

    def test_login_succeeds_after_activation_and_sets_cookies(self):
        """
        Active users get both access and refresh tokens as HttpOnly cookies.
        """

        self._activate()

        resp = self.client.post(self.login_url, {'email': self.email, 'password': self.password}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(resp.data.get('detail'), 'Login successful')
        self.assertIn('user', resp.data)
        self.assertEqual(resp.data['user']['id'], self.user.id)
        self.assertEqual(resp.data['user']['username'], self.email)

        self.assertIn('access_token', resp.cookies)
        self.assertIn('refresh_token', resp.cookies)
        self.assertTrue(resp.cookies['access_token'].value)
        self.assertTrue(resp.cookies['refresh_token'].value)

    def test_login_wrong_password_returns_401(self):
        """
        Wrong password should be rejected with 401.
        """

        self._activate()

        resp = self.client.post(self.login_url, {'email': self.email, 'password': 'wrongpass'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', resp.data)

    def test_login_missing_fields_returns_400(self):
        """
        Missing body yields 400 with a helpful message.
        """

        resp = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', resp.data)
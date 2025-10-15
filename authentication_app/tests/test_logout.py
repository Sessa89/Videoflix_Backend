"""
Tests for logout endpoint.

Covers:
- Successful logout blacklists the refresh token and clears cookies.
- Missing refresh cookie returns 400.
- Invalid refresh token returns 400.
"""

from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

class LogoutEndpointTests(APITestCase):
    """
    E2E tests for /api/logout/
    """

    def setUp(self):
        self.register_url = reverse('api-register')
        self.activate_url = reverse('api-activate')
        self.login_url    = reverse('api-login')
        self.logout_url   = reverse('api-logout')

        self.email = 'logout@test.com'
        self.password = 'securepassword'

        r = self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password, 'confirmed_password': self.password},
            format='json',
        )
        uid = urlsafe_base64_encode(force_bytes(r.data['user']['id']))
        token = r.data['token']

        a = self.client.post(self.activate_url, {'uid': uid, 'token': token}, format='json')
        self.assertEqual(a.status_code, status.HTTP_200_OK)

        login = self.client.post(self.login_url, {'email': self.email, 'password': self.password}, format='json')
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn('refresh_token', login.cookies)

    def test_logout_blacklists_refresh_and_deletes_cookies(self):
        """
        Refresh token should be blacklisted and cookies cleared after logout.
        """

        refresh_cookie = self.client.cookies.get('refresh_token').value
        jti = RefreshToken(refresh_cookie)['jti']

        resp = self.client.post(self.logout_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data['detail'],
            'Logout successful! All tokens will be deleted. Refresh token is now invalid.',
        )

        self.assertTrue(BlacklistedToken.objects.filter(token__jti=jti).exists())

        self.assertNotIn('Set-Cookie', resp.headers.get('access_token', ''))

    def test_logout_without_refresh_cookie_returns_400(self):
        """
        Missing refresh cookie should be rejected with 400.
        """

        self.client.cookies.clear()
        resp = self.client.post(self.logout_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Refresh token', resp.data['detail'])

    def test_logout_with_invalid_refresh_token_returns_400(self):
        """
        Invalid/forged refresh cookie should return 400.
        """

        self.client.cookies['refresh_token'] = 'invalid'
        resp = self.client.post(self.logout_url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid refresh token', resp.data['detail'])
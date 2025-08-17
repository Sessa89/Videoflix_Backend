from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase

class CookieTokenRefreshTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('api-register')
        self.activate_url = reverse('api-activate')
        self.login_url    = reverse('api-login')
        self.refresh_url  = reverse('token-refresh')
        self.logout_url   = reverse('api-logout')

        self.email = 'refresh@test.com'
        self.password = 'securepassword'

        r = self.client.post(self.register_url, {
            'email': self.email, 'password': self.password, 'confirmed_password': self.password
        }, format='json')
        uid = urlsafe_base64_encode(force_bytes(r.data['user']['id']))
        token = r.data['token']

        a = self.client.post(self.activate_url, {'uid': uid, 'token': token}, format='json')
        self.assertEqual(a.status_code, status.HTTP_200_OK)

        login = self.client.post(self.login_url, {'email': self.email, 'password': self.password}, format='json')
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn('refresh_token', login.cookies)
        self.old_access = self.client.cookies.get('access_token').value

    def test_refresh_success_sets_new_access_cookie_and_returns_access(self):
        resp = self.client.post(self.refresh_url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('detail'), 'Token refreshed')
        self.assertIn('access', resp.data)
        
        self.assertIn('access_token', resp.cookies)
        self.assertTrue(resp.cookies['access_token'].value)
        self.assertNotEqual(resp.data['access'], self.old_access)

    def test_refresh_without_cookie_returns_400(self):
        self.client.cookies.clear()
        resp = self.client.post(self.refresh_url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Refresh token', resp.data['detail'])

    def test_refresh_with_invalid_cookie_returns_401(self):
        self.client.cookies['refresh_token'] = 'invalid'
        resp = self.client.post(self.refresh_url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Invalid refresh token', resp.data['detail'])

    def test_refresh_after_logout_is_unauthorized(self):
        lo = self.client.post(self.logout_url)
        self.assertEqual(lo.status_code, status.HTTP_200_OK)

        resp = self.client.post(self.refresh_url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
"""
Tests for account activation via GET (URL link) and POST (JSON payload).

Covers:
- GET /api/activate/<uid>/<token>/ success and invalid token.
- POST /api/activate/ success and invalid uid.
"""

from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

class ActivateAccountTests(APITestCase):
    """
    Integration tests for both activation paths.
    """

    def setUp(self):
        self.register_url = reverse('api-register')
        self.activate_post_url = reverse('api-activate')
        self.email = 'activate@example.com'
        self.password = 'securepassword'

        reg = self.client.post(
            self.register_url,
            {'email': self.email, 'password': self.password, 'confirmed_password': self.password},
            format='json',
        )
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)

        self.user = User.objects.get(email=self.email)
        self.assertFalse(self.user.is_active)

        self.token = reg.data['token']
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_activate_via_get_succeeds_and_sets_user_active(self):
        """
        GET flow: visiting the activation URL should activate the user.
        """

        url = reverse('api-activate-link', kwargs={'uidb64': self.uidb64, 'token': self.token})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('message'), 'Account successfully activated.')

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_activate_via_get_with_invalid_token_returns_400(self):
        """
        GET flow: invalid token is rejected.
        """

        bad_url = reverse('api-activate-link', kwargs={'uidb64': self.uidb64, 'token': 'invalid-token'})
        resp = self.client.get(bad_url)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get('message'), 'Activation failed.')

    def test_activate_via_post_succeeds_and_sets_user_active(self):
        """
        POST flow: activation via JSON body {uid, token}.
        """

        email2 = 'activate2@example.com'
        reg2 = self.client.post(
            self.register_url,
            {'email': email2, 'password': self.password, 'confirmed_password': self.password},
            format='json',
        )
        self.assertEqual(reg2.status_code, status.HTTP_201_CREATED)
        user2 = User.objects.get(email=email2)
        uid2 = urlsafe_base64_encode(force_bytes(user2.pk))
        token2 = reg2.data['token']

        resp = self.client.post(self.activate_post_url, {'uid': uid2, 'token': token2}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('detail'), 'Account activated.')

        user2.refresh_from_db()
        self.assertTrue(user2.is_active)

    def test_activate_via_post_with_invalid_uid_returns_400(self):
        """
        POST flow: invalid base64 uid is rejected.
        """

        resp = self.client.post(self.activate_post_url, {'uid': 'invalid', 'token': self.token}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid', resp.data.get('detail', ''))
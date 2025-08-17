from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class RegisterEndpointTests(APITestCase):
    def setUp(self):
        self.url = reverse('api-register')
        self.payload = {
            'email': 'user@example.com',
            'password': 'securepassword',
            'confirmed_password': 'securepassword',
        }

    def test_register_success_returns_201_and_expected_payload(self):
        resp = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', resp.data)
        self.assertIn('token', resp.data)
        self.assertEqual(set(resp.data['user'].keys()), {'id', 'email'})
        self.assertEqual(resp.data['user']['email'], self.payload['email'])

        user = User.objects.get(email=self.payload['email'])
        self.assertFalse(user.is_active)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate your Videoflix account', mail.outbox[0].subject)
        self.assertIn(self.payload['email'], mail.outbox[0].to)

    def test_register_password_mismatch_returns_400(self):
        bad = dict(self.payload)
        bad['confirmed_password'] = 'different'
        resp = self.client.post(self.url, bad, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', resp.data)

    def test_register_duplicate_email_returns_400(self):
        User.objects.create_user(
            username=self.payload['email'],
            email=self.payload['email'],
            password='somepassword123',
        )

        resp = self.client.post(self.url, self.payload, format='json')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', resp.data)
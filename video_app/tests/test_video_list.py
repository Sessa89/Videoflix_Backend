"""
Tests for listing videos.

Covers:
- Anonymous user is rejected with 401.
- Authenticated user gets a list of serialized video metadata.
"""

from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase
from video_app.models import Video

class VideoListTests(APITestCase):
    """
    E2E tests for GET /api/video/
    """

    def setUp(self):
        
        self.register_url = reverse('api-register')
        self.activate_url = reverse('api-activate')
        self.login_url    = reverse('api-login')
        self.list_url     = reverse('video-list')

        self.email = 'viewer@example.com'
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
        self.assertIn('access_token', login.cookies)

        Video.objects.create(
            title="Movie Title",
            description="Movie Description",
            thumbnail_url="http://example.com/media/thumbnail/image.jpg",
            category="DRAMA",
        )
        Video.objects.create(
            title="Another Movie",
            description="Another Description",
            thumbnail_url="http://example.com/media/thumbnail/image2.jpg",
            category="ROMANCE",
        )

    def test_list_requires_authentication(self):
        """
        Anonymous requests must be rejected with 401 Unauthorized.
        """

        from rest_framework.test import APIClient
        anon = APIClient()
        resp = anon.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_returns_video_metadata(self):
        """
        Authenticated requests receive a list of serialized video metadata.
        """

        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)
        self.assertEqual(len(resp.data), 2)

        item = resp.data[0]
        self.assertEqual(set(item.keys()),
                         {"id", "created_at", "title", "description", "thumbnail_url", "category"})
        self.assertIn(item["category"], ["Drama", "Romance"])
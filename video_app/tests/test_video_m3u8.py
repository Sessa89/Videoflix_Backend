"""
Tests for serving HLS master playlist (index.m3u8).

Covers:
- Requires auth (401 for anonymous).
- 404 when manifest file is missing.
- 200 with correct content type when manifest exists.
"""

import tempfile
from pathlib import Path
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status

class VideoM3U8Tests(APITestCase):
    """
    E2E tests for GET /api/video/<movie_id>/<resolution>/index.m3u8
    """

    def _login(self):
        """
        Helper to create and authenticate a user for protected endpoints.
        """

        register_url = reverse('api-register')
        activate_url = reverse('api-activate')
        login_url    = reverse('api-login')

        email = 'viewer@test.com'
        pw = 'securepassword'

        r = self.client.post(register_url, {
            'email': email, 'password': pw, 'confirmed_password': pw
        }, format='json')
        uid = urlsafe_base64_encode(force_bytes(r.data['user']['id']))
        token = r.data['token']
        a = self.client.post(activate_url, {'uid': uid, 'token': token}, format='json')
        self.assertEqual(a.status_code, status.HTTP_200_OK)
        login = self.client.post(login_url, {'email': email, 'password': pw}, format='json')
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    @override_settings(HLS_ALLOWED_RESOLUTIONS={'720p'})
    def test_404_if_file_missing(self):
        """
        If the manifest is not present on disk, return 404.
        """

        self._login()
        url = reverse('video-m3u8', kwargs={'movie_id': 1, 'resolution': '720p'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_serves_manifest_when_present(self):
        """
        When the m3u8 exists, serve it with the expected MIME type.
        """

        self._login()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            movie_id = 5
            res = '720p'
            manifest_dir = root / str(movie_id) / res
            manifest_dir.mkdir(parents=True, exist_ok=True)
            m3u8 = manifest_dir / 'index.m3u8'
            sample = '#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n'
            m3u8.write_text(sample, encoding='utf-8')

            with override_settings(HLS_ROOT=root, HLS_ALLOWED_RESOLUTIONS={'720p'}):
                url = reverse('video-m3u8', kwargs={'movie_id': movie_id, 'resolution': res})
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, status.HTTP_200_OK)
                self.assertEqual(resp['Content-Type'], 'application/vnd.apple.mpegurl')
                self.assertIn('#EXTM3U', resp.content.decode('utf-8'))

    def test_401_without_auth(self):
        """
        Anonymous requests are rejected.
        """

        url = reverse('video-m3u8', kwargs={'movie_id': 1, 'resolution': '720p'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
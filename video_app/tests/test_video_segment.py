import tempfile
from pathlib import Path
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status

class VideoSegmentTests(APITestCase):
    def _login(self):
        reg = reverse('api-register')
        act = reverse('api-activate')
        log = reverse('api-login')

        email = 'seg@test.com'
        pw = 'securepassword'
        r = self.client.post(reg, {'email': email, 'password': pw, 'confirmed_password': pw}, format='json')
        uid = urlsafe_base64_encode(force_bytes(r.data['user']['id']))
        token = r.data['token']
        self.client.post(act, {'uid': uid, 'token': token}, format='json')
        self.client.post(log, {'email': email, 'password': pw}, format='json')

    def test_requires_auth(self):
        url = reverse('video-segment', kwargs={'movie_id': 1, 'resolution': '720p', 'segment': '000.ts'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(HLS_ALLOWED_RESOLUTIONS={'720p'}, HLS_ALLOWED_SEGMENT_EXTS={'.ts'})
    def test_404_when_not_found(self):
        self._login()
        url = reverse('video-segment', kwargs={'movie_id': 2, 'resolution': '720p', 'segment': '000.ts'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_serves_segment(self):
        self._login()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            movie_id = 7
            res = '720p'
            (root / str(movie_id) / res).mkdir(parents=True, exist_ok=True)
            seg_file = root / str(movie_id) / res / '000.ts'
            seg_bytes = b'\x00\x00\x01\xba\x44\x00\x04'
            seg_file.write_bytes(seg_bytes)

            with override_settings(HLS_ROOT=root, HLS_ALLOWED_RESOLUTIONS={'720p'}, HLS_ALLOWED_SEGMENT_EXTS={'.ts'}):
                url = reverse('video-segment', kwargs={'movie_id': movie_id, 'resolution': res, 'segment': '000.ts'})
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, status.HTTP_200_OK)
                self.assertEqual(resp['Content-Type'], 'video/MP2T')
                self.assertEqual(resp.getvalue(), seg_bytes)

    def test_rejects_bad_segment_name(self):
        self._login()
        with override_settings(HLS_ALLOWED_RESOLUTIONS={'720p'}):
            resp = self.client.get('/api/video/1/720p/../hack.ts/')
            self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_rejects_bad_extension(self):
        self._login()
        with override_settings(HLS_ALLOWED_RESOLUTIONS={'720p'}, HLS_ALLOWED_SEGMENT_EXTS={'.ts'}):
            resp = self.client.get('/api/video/1/720p/000.m4s/')
            self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
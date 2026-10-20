import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Hotspot, KontakDarurat, LaporanWarga

# File GIF 1x1 valid untuk uji upload foto
TINY_GIF = (
    b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00'
    b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hotspot = Hotspot.objects.create(
            provinsi='KALTENG', lokasi_deskripsi='Palangka Raya',
            latitude=-2.21, longitude=113.92, tingkat_kepercayaan=90, status='AWAS',
        )
        cls.kontak = KontakDarurat.objects.create(
            nama_instansi='BPBD Kalteng', provinsi='KALTENG', nomor_telepon='112',
        )

    def test_dashboard_200(self):
        resp = self.client.get(reverse('tracker:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Kalimantan')

    def test_kontak_page(self):
        resp = self.client.get(reverse('tracker:kontak'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'BPBD Kalteng')


class ApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Hotspot.objects.create(
            provinsi='KALTENG', lokasi_deskripsi='Palangka Raya',
            latitude=-2.21, longitude=113.92, status='AWAS',
        )
        Hotspot.objects.create(
            provinsi='KALTIM', lokasi_deskripsi='Samarinda',
            latitude=-0.50, longitude=117.15, status='SIAGA',
        )
        LaporanWarga.objects.create(
            judul='Api di lahan', pelapor_nama='Budi', pelapor_kontak='0812',
            provinsi='KALTENG', deskripsi='Asap tebal', status='VERIFIED',
            latitude=-2.2, longitude=113.9,
        )
        LaporanWarga.objects.create(
            judul='Belum verifikasi', pelapor_nama='Ani', pelapor_kontak='0813',
            provinsi='KALTIM', deskripsi='Baru dilaporkan', status='PENDING',
        )
        KontakDarurat.objects.create(
            nama_instansi='BPBD Kalteng', provinsi='KALTENG', nomor_telepon='112',
        )

    def test_api_hotspots(self):
        resp = self.client.get(reverse('tracker:api_hotspots'))
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['hotspots']), 2)

    def test_api_hotspots_filter_provinsi(self):
        resp = self.client.get(reverse('tracker:api_hotspots') + '?provinsi=KALTENG')
        data = json.loads(resp.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['hotspots'][0]['provinsi'], 'KALTENG')

    def test_api_hotspots_filter_status(self):
        resp = self.client.get(reverse('tracker:api_hotspots') + '?status=SIAGA')
        data = json.loads(resp.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['hotspots'][0]['status'], 'SIAGA')

    def test_api_laporan_excludes_pending(self):
        resp = self.client.get(reverse('tracker:api_laporan'))
        data = json.loads(resp.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['laporan'][0]['status'], 'VERIFIED')

    def test_api_kontak(self):
        resp = self.client.get(reverse('tracker:api_kontak'))
        data = json.loads(resp.content)
        self.assertEqual(data['count'], 1)

    def test_export_hotspots_geojson(self):
        resp = self.client.get(reverse('tracker:export_hotspots'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/geo+json')
        data = json.loads(resp.content)
        self.assertEqual(data['type'], 'FeatureCollection')
        self.assertEqual(len(data['features']), 2)
        self.assertEqual(data['features'][0]['geometry']['type'], 'Point')

    def test_export_laporan_geojson(self):
        resp = self.client.get(reverse('tracker:export_laporan'))
        data = json.loads(resp.content)
        self.assertEqual(len(data['features']), 1)  # PENDING tanpa lokasi publik tidak ikut


class LaporanTests(TestCase):
    def test_form_get(self):
        resp = self.client.get(reverse('tracker:laporan_create'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'csrfmiddlewaretoken')

    def test_form_post_valid(self):
        resp = self.client.post(reverse('tracker:laporan_create'), {
            'judul': 'Kebakaran lahan dekat rumah',
            'pelapor_nama': 'Tes Pelapor',
            'pelapor_kontak': '081234567890',
            'provinsi': 'KALTENG',
            'deskripsi': 'Asap tebal terlihat dari belakang rumah.',
            'latitude': '-2.21',
            'longitude': '113.92',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(LaporanWarga.objects.count(), 1)
        laporan = LaporanWarga.objects.get()
        self.assertEqual(laporan.status, 'PENDING')
        self.assertTrue(resp.url.endswith(f'/laporan/{laporan.pk}/sukses/'))

    def test_form_post_with_photo(self):
        foto = SimpleUploadedFile('test.gif', TINY_GIF, content_type='image/gif')
        resp = self.client.post(reverse('tracker:laporan_create'), {
            'judul': 'Dengan foto',
            'pelapor_nama': 'Tes',
            'pelapor_kontak': '0812',
            'provinsi': 'KALTIM',
            'deskripsi': 'Deskripsi tes dengan foto.',
            'foto': foto,
        })
        self.assertEqual(resp.status_code, 302)
        laporan = LaporanWarga.objects.get()
        self.assertTrue(laporan.foto)

    def test_form_post_invalid_mismatched_coords(self):
        resp = self.client.post(reverse('tracker:laporan_create'), {
            'judul': 'Koordinat salah',
            'pelapor_nama': 'Tes',
            'pelapor_kontak': '0812',
            'provinsi': 'KALBAR',
            'deskripsi': 'Hanya latitude tanpa longitude.',
            'latitude': '-0.1',
            'longitude': '',
        })
        self.assertEqual(resp.status_code, 200)  # form redisplays
        self.assertEqual(LaporanWarga.objects.count(), 0)

    def test_laporan_detail_visibility(self):
        publik = LaporanWarga.objects.create(
            judul='Publik', pelapor_nama='A', pelapor_kontak='0812',
            provinsi='KALTENG', deskripsi='x', status='VERIFIED',
        )
        pending = LaporanWarga.objects.create(
            judul='Pending', pelapor_nama='B', pelapor_kontak='0813',
            provinsi='KALTENG', deskripsi='x', status='PENDING',
        )
        resp = self.client.get(reverse('tracker:laporan_detail', args=[publik.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Publik')

        resp = self.client.get(reverse('tracker:laporan_detail', args=[pending.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_laporan_list_excludes_pending(self):
        LaporanWarga.objects.create(
            judul='Publik', pelapor_nama='A', pelapor_kontak='0812',
            provinsi='KALTENG', deskripsi='x', status='VERIFIED',
        )
        LaporanWarga.objects.create(
            judul='Pending', pelapor_nama='B', pelapor_kontak='0813',
            provinsi='KALTENG', deskripsi='x', status='PENDING',
        )
        resp = self.client.get(reverse('tracker:laporan_list'))
        self.assertContains(resp, 'Publik')
        self.assertNotContains(resp, 'Pending')

    def test_laporan_list_filter_provinsi(self):
        LaporanWarga.objects.create(
            judul='Kalteng punya', pelapor_nama='A', pelapor_kontak='0812',
            provinsi='KALTENG', deskripsi='x', status='VERIFIED',
        )
        LaporanWarga.objects.create(
            judul='Kaltim punya', pelapor_nama='B', pelapor_kontak='0813',
            provinsi='KALTIM', deskripsi='x', status='VERIFIED',
        )
        resp = self.client.get(reverse('tracker:laporan_list') + '?provinsi=KALTENG')
        self.assertContains(resp, 'Kalteng punya')
        self.assertNotContains(resp, 'Kaltim punya')

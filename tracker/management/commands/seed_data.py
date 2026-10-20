import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import Hotspot, KontakDarurat, LaporanWarga

# Titik pusat (lat, lng) per provinsi untuk menyebar hotspot realistis
PROVINSI_PUSAT = {
    'KALBAR': (-0.05, 109.20),
    'KALTENG': (-1.90, 113.40),
    'KALSEL': (-3.10, 115.00),
    'KALTIM': (-0.80, 117.00),
    'KALTARA': (2.60, 117.30),
}

LOKASI_PER_PROVINSI = {
    'KALBAR': [
        'Kab. Ketapang', 'Kab. Sanggau', 'Kab. Sintang', 'Kota Pontianak',
        'Kab. Kapuas Hulu', 'Kab. Bengkayang', 'Kab. Landak',
    ],
    'KALTENG': [
        'Kab. Pulang Pisau', 'Kab. Kapuas', 'Kota Palangka Raya',
        'Kab. Gunung Mas', 'Kab. Kotawaringin Barat', 'Kab. Barito Selatan',
        'Kab. Katingan',
    ],
    'KALSEL': [
        'Kab. Tanah Laut', 'Kab. Banjar', 'Kota Banjarmasin',
        'Kab. Kotabaru', 'Kab. Hulu Sungai Selatan', 'Kab. Tabalong',
    ],
    'KALTIM': [
        'Kab. Kutai Kartanegara', 'Kota Samarinda', 'Kab. Penajam Paser Utara',
        'Kab. Kutai Barat', 'Kota Balikpapan', 'Kab. Berau',
    ],
    'KALTARA': [
        'Kab. Bulungan', 'Kab. Tana Tidung', 'Kota Tarakan',
        'Kab. Malinau', 'Kab. Nunukan',
    ],
}

KONTAK_SEED = [
    ('KALBAR', [
        ('BPBD Provinsi Kalimantan Barat', '0561-742112', 'Jl. Jenderal Sudirman, Pontianak'),
        ('Dinas Pemadam Kebakaran Kota Pontianak', '0561-736119', 'Jl. Tanjung Harapan, Pontianak'),
        ('Manggala Agni KPDAS Kapuas Hulu', '0562-22145', 'Nanga Pinoh, Melawi'),
    ]),
    ('KALTENG', [
        ('BPBD Provinsi Kalimantan Tengah', '0536-3227633', 'Jl. Tjilik Riwut, Palangka Raya'),
        ('Dinas Pemadam Kebakaran Palangka Raya', '0536-322344', 'Jl. G.Obos, Palangka Raya'),
        ('Manggala Agni KPDAS Kalteng', '0536-3233517', 'Jl. Imam Bonjol, Palangka Raya'),
        ('RSUD dr. Doris Sylvanus', '0536-3225555', 'Jl. Tinggang, Palangka Raya'),
    ]),
    ('KALSEL', [
        ('BPBD Provinsi Kalimantan Selatan', '0511-3353345', 'Jl. Jenderal Ahmad Yani, Banjarmasin'),
        ('Dinas Pemadam Kebakaran Banjarmasin', '0511-3356666', 'Jl. A. Yani Km 13, Banjarmasin'),
        ('Manggala Agni KPDAS Kalsel', '0511-3357890', 'Jl. Pangeran Antasari, Banjarmasin'),
    ]),
    ('KALTIM', [
        ('BPBD Provinsi Kalimantan Timur', '0542-422101', 'Jl. Gajah Mada, Samarinda'),
        ('Dinas Pemadam Kebakaran Samarinda', '0542-421119', 'Jl. Kesuma Bangga, Samarinda'),
        ('Manggala Agni KPDAS Kaltim', '0542-423456', 'Jl. Mulawarman, Samarinda'),
        ('RSUD AW Sjahranie', '0542-422555', 'Jl. P. Diponegoro, Samarinda'),
    ]),
    ('KALTARA', [
        ('BPBD Provinsi Kalimantan Utara', '0551-22123', 'Jl. Jenderal Sudirman, Tarakan'),
        ('Dinas Pemadam Kebakaran Tarakan', '0551-21153', 'Jl. Mulawarman, Tarakan'),
        ('Manggala Agni KPDAS Kaltara', '0551-22990', 'Jl. Pembangunan, Tarakan'),
    ]),
]

LAPORAN_SEED = [
    ('Asap pekat di kawasan lahan gambut', 'KALTENG', 'Asap sangat tebal terlihat sejak pagi hari di sekitar lahan gambut dekat Desa Bunut. Jarak pandang menurun drastis. Warga mulai mengungsi sementara ke rumah kerabat.', 'VERIFIED'),
    ('Kebakaran lahan di tepi jalan poros', 'KALTIM', 'Lahan semak belukar terbakar di sisi jalan poros menuju kebun kelapa sawit. Api belum besar namun angin kencang dikhawatirkan memperluas area.', 'HANDLED'),
    ('Titik api terdeteksi di dekat kebun karet', 'KALBAR', 'Sesuai laporan warga, terlihat asap tipis dari arah kebun karet. Sudah dikonfirmasi warga sekitar bahwa ada pembakaran sampah yang menjalar.', 'RESOLVED'),
    ('Kebakaran hutan di kawasan perbukitan', 'KALSEL', 'Api terlihat di kawasan perbukitan dekat kampung. Warga bersama warga RT berusaha memadamkan dengan alat seadanya. Membutuhkan bantuan waterbomb.', 'VERIFIED'),
    ('Karhutla di area eksplorasi tambang', 'KALTARA', 'Titik api terdeteksi di area eksplorasi tambang batu bara. Asap hitam pekat terlihat dari jarak 2 km. Segera hubungi petugas Manggala Agni.', 'PENDING'),
    ('Pembakaran sampah menjalar ke lahan', 'KALTENG', 'Warga membakar sampah namun api menjalar ke lahan sekitar akibat angin. Luas area terbakar sekitar 500 m². Tidak ada korban jiwa.', 'VERIFIED'),
    ('Api di areal persawahan', 'KALBAR', 'Petani membakar jerami padi setelah panen, namun api menjalar ke pematang dan lahan di sekitarnya. Sudah dipadamkan warga.', 'RESOLVED'),
    ('Asap dari arah hutan produksi', 'KALTIM', 'Asap tebal terlihat dari arah hutan produksi PT. X. Masyarakat curiga ada pembukaan lahan ilegal. Meminta investigasi petugas.', 'HANDLED'),
    ('Kebakaran semak di pinggir kota', 'KALSEL', 'Semak belukar di lahan kosong pinggiran kota terbakar. Api sudah dipadamkan damkar setengah jam kemudian. Tidak ada korban jiwa.', 'RESOLVED'),
    ('Laporan asap dari warga pesisir', 'KALBAR', 'Warga pesisir melihat asap dari arah daratan. Setelah dicek, ternyata kebakaran lahan kecil di area rumput.', 'VERIFIED'),
]


def _spread(base, delta=0.6):
    return base + random.uniform(-delta, delta)


class Command(BaseCommand):
    help = 'Mengisi database dengan data contoh: hotspot, kontak darurat, laporan warga, dan superuser demo.'

    def add_arguments(self, parser):
        parser.add_argument('--with-superuser', action='store_true', help='Buat superuser demo admin/admin12345.')

    def handle(self, *args, **options):
        random.seed(42)  # deterministik

        if Hotspot.objects.exists():
            self.stdout.write(self.style.WARNING('Hotspot sudah ada — lewati.'))
        else:
            self._seed_hotspots()

        if KontakDarurat.objects.exists():
            self.stdout.write(self.style.WARNING('KontakDarurat sudah ada — lewati.'))
        else:
            self._seed_kontak()

        if LaporanWarga.objects.exists():
            self.stdout.write(self.style.WARNING('LaporanWarga sudah ada — lewati.'))
        else:
            self._seed_laporan()

        if options['with_superuser']:
            self._seed_superuser()

        self.stdout.write(self.style.SUCCESS('Seed data selesai.'))

    def _seed_hotspots(self):
        now = timezone.now()
        count = 0
        for provinsi, (plat, plng) in PROVINSI_PUSAT.items():
            for i in range(8):
                lat = _spread(plat)
                lng = _spread(plng, 0.8)
                Hotspot.objects.create(
                    provinsi=provinsi,
                    lokasi_deskripsi=random.choice(LOKASI_PER_PROVINSI[provinsi]),
                    latitude=round(lat, 6),
                    longitude=round(lng, 6),
                    tingkat_kepercayaan=random.randint(55, 98),
                    status=random.choice(['AWAS', 'AWAS', 'SIAGA']),
                    waktu_terdeteksi=now - timedelta(hours=random.randint(1, 200)),
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f'{count} hotspot dibuat.'))

    def _seed_kontak(self):
        count = 0
        for provinsi, instansi_list in KONTAK_SEED:
            for nama, telp, alamat in instansi_list:
                KontakDarurat.objects.create(
                    nama_instansi=nama,
                    provinsi=provinsi,
                    nomor_telepon=telp,
                    alamat=alamat,
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f'{count} kontak darurat dibuat.'))

    def _seed_laporan(self):
        now = timezone.now()
        count = 0
        for judul, provinsi, deskripsi, status in LAPORAN_SEED:
            plat, plng = PROVINSI_PUSAT[provinsi]
            LaporanWarga.objects.create(
                judul=judul,
                pelapor_nama=random.choice(['Budi Santoso', 'Siti Aminah', 'Agus Prasetyo', 'Dewi Lestari', 'Rahmat Hidayat']),
                pelapor_kontak=f'08{random.randint(1111111111, 9999999999)}',
                provinsi=provinsi,
                latitude=round(_spread(plat), 6),
                longitude=round(_spread(plng, 0.8), 6),
                deskripsi=deskripsi,
                status=status,
                created_at=now - timedelta(hours=random.randint(2, 300)),
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f'{count} laporan warga dibuat.'))

    def _seed_superuser(self):
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Superuser "admin" sudah ada.'))
            return
        User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
        self.stdout.write(self.style.SUCCESS('Superuser demo dibuat: admin / admin12345'))

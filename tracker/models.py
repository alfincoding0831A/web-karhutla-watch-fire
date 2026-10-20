from django.db import models

PROVINSI_CHOICES = [
    ('KALBAR', 'Kalimantan Barat'),
    ('KALTENG', 'Kalimantan Tengah'),
    ('KALSEL', 'Kalimantan Selatan'),
    ('KALTIM', 'Kalimantan Timur'),
    ('KALTARA', 'Kalimantan Utara'),
]

STATUS_LAPORAN = [
    ('PENDING', 'Menunggu Verifikasi'),
    ('VERIFIED', 'Terverifikasi / Aktif'),
    ('HANDLED', 'Dalam Penanganan'),
    ('RESOLVED', 'Padam / Selesai'),
]

STATUS_BADGE = {
    'PENDING': 'amber',
    'VERIFIED': 'orange',
    'HANDLED': 'sky',
    'RESOLVED': 'emerald',
}


class Hotspot(models.Model):
    STATUS_CHOICES = [('SIAGA', 'Siaga'), ('AWAS', 'Awas/Terbakar')]

    provinsi = models.CharField(max_length=10, choices=PROVINSI_CHOICES)
    lokasi_deskripsi = models.CharField(max_length=255, help_text='Nama Desa/Kecamatan/Kabupaten')
    latitude = models.FloatField()
    longitude = models.FloatField()
    tingkat_kepercayaan = models.IntegerField(default=80, help_text='Persentase Confidence Level (0-100%)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AWAS')
    waktu_terdeteksi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-waktu_terdeteksi']
        indexes = [
            models.Index(fields=['provinsi', 'status']),
            models.Index(fields=['-waktu_terdeteksi']),
        ]
        verbose_name = 'Hotspot'
        verbose_name_plural = 'Hotspot'

    def __str__(self):
        return f'{self.get_provinsi_display()} - {self.lokasi_deskripsi} ({self.status})'

    @property
    def is_awas(self):
        return self.status == 'AWAS'


class LaporanWarga(models.Model):
    judul = models.CharField(max_length=200)
    pelapor_nama = models.CharField(max_length=100)
    pelapor_kontak = models.CharField(max_length=50, help_text='Nomor WhatsApp/HP')
    provinsi = models.CharField(max_length=10, choices=PROVINSI_CHOICES)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    deskripsi = models.TextField()
    foto = models.ImageField(upload_to='laporan_karhutla/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_LAPORAN, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'provinsi']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Laporan Warga'
        verbose_name_plural = 'Laporan Warga'

    def __str__(self):
        return f'[{self.status}] {self.judul} - {self.get_provinsi_display()}'

    @property
    def badge_color(self):
        return STATUS_BADGE.get(self.status, 'slate')

    @property
    def is_public(self):
        return self.status != 'PENDING'

    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None


class KontakDarurat(models.Model):
    nama_instansi = models.CharField(max_length=150)
    provinsi = models.CharField(max_length=10, choices=PROVINSI_CHOICES)
    nomor_telepon = models.CharField(max_length=30)
    alamat = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['provinsi', 'nama_instansi']
        verbose_name = 'Kontak Darurat'
        verbose_name_plural = 'Kontak Darurat'

    def __str__(self):
        return f'{self.nama_instansi} ({self.get_provinsi_display()})'

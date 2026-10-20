# 🔥 Kalimantan FireWatch

Sistem pemantauan dan pelaporan kebakaran hutan & lahan (karhutla) di 5 provinsi Pulau Kalimantan — dibangun dengan **Django**.

## Fitur

| Fitur | Keterangan |
|---|---|
| 🗺️ Dashboard Peta Live | Peta Leaflet dengan titik hotspot, filter provinsi & status, refresh otomatis tiap 60 detik |
| 🚨 Form Laporan Warga | Form publik dengan unggah foto, pemilih lokasi di peta, dan deteksi GPS perangkat |
| ✅ Alur Verifikasi Admin | Aksi bulk di Django admin: Verifikasi → Ditangani → Padam/Selesai |
| 🆘 Kontak Darurat | Daftar BPBD / Damkar / Manggala Agni per provinsi dengan klik-telepon |
| 📤 Ekspor Data Terbuka | Unduh GeoJSON (hotspot & laporan) + API JSON terbuka |
| 🌑 Tema Gelap Modern | UI Tailwind CSS dark theme, responsif mobile |

## Halaman Publik

- `/` — Dashboard peta hotspot live
- `/laporan/` — Daftar laporan terverifikasi (filter per provinsi)
- `/laporan/baru/` — Form buat laporan baru
- `/laporan/<id>/` — Detail laporan
- `/kontak/` — Kontak darurat per provinsi

## API JSON

- `/api/hotspots/?provinsi=KALTENG&status=AWAS` — Daftar hotspot
- `/api/laporan/?provinsi=KALTIM&status=VERIFIED` — Daftar laporan publik
- `/api/kontak/?provinsi=KALSEL` — Kontak darurat

## Ekspor GeoJSON

- `/api/export/hotspots.geojson` — Hotspot sebagai FeatureCollection
- `/api/export/laporan.geojson` — Laporan terverifikasi berkoordinat

## Cara Menjalankan

```bash
# 1. Virtual environment & dependensi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Migrasi database
python manage.py migrate

# 3. Isi data contoh (hotspot, kontak, laporan, superuser demo)
python manage.py seed_data --with-superuser

# 4. Jalankan server
python manage.py runserver
```

Buka **http://127.0.0.1:8000/** — panel admin di **http://127.0.0.1:8000/admin/** (login: `admin` / `admin12345`, hanya untuk demo).

## Menjalankan Test

```bash
python manage.py test tracker
```

## Struktur

```
config/                  # Konfigurasi proyek Django
tracker/
├── models.py            # Hotspot, LaporanWarga, KontakDarurat
├── forms.py             # Form laporan warga
├── views.py             # Halaman publik + API JSON + ekspor GeoJSON
├── urls.py              # Semua rute
├── admin.py             # Aksi bulk verifikasi & pratinjau foto
├── tests.py             # Test smoke semua endpoint
├── management/commands/seed_data.py  # Data contoh 5 provinsi
└── templates/tracker/   # base, dashboard, form, list, detail, success, kontak
```

## Catatan Produksi

- Ganti `SECRET_KEY` dan set `DEBUG = False` di `config/settings.py`
- Isi `ALLOWED_HOSTS`
- Gunakan PostgreSQL sebagai database
- Sajikan media lewat web server (bukan Django) di production
# web-karhutla-watch-fire

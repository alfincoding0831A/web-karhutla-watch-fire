from django import forms

from .models import LaporanWarga

FIELD_CLASS = (
    'w-full bg-slate-900/60 border border-slate-700 rounded-lg px-4 py-2.5 '
    'text-sm text-slate-100 placeholder-slate-500 transition '
    'focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent'
)


class LaporanWargaForm(forms.ModelForm):
    class Meta:
        model = LaporanWarga
        fields = [
            'judul', 'pelapor_nama', 'pelapor_kontak', 'provinsi',
            'deskripsi', 'foto', 'latitude', 'longitude',
        ]
        widgets = {
            'judul': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'Contoh: Asap tebal di dekat Jalan Tjilik Riwut',
            }),
            'pelapor_nama': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'Nama lengkap pelapor',
            }),
            'pelapor_kontak': forms.TextInput(attrs={
                'class': FIELD_CLASS,
                'placeholder': 'Nomor WhatsApp / HP yang aktif',
            }),
            'provinsi': forms.Select(attrs={'class': FIELD_CLASS}),
            'deskripsi': forms.Textarea(attrs={
                'class': FIELD_CLASS,
                'rows': 5,
                'placeholder': 'Jelaskan kondisi di lapangan: arah angin, luas area terbakar, barang berharga di sekitar, dll.',
            }),
            'foto': forms.ClearableFileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*',
            }),
            'latitude': forms.HiddenInput(attrs={'id': 'id_latitude'}),
            'longitude': forms.HiddenInput(attrs={'id': 'id_longitude'}),
        }

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get('latitude')
        lng = cleaned.get('longitude')
        if (lat is None) != (lng is None):
            self.add_error(None, 'Latitude dan longitude harus diisi bersamaan. Klik peta untuk menandai lokasi.')
        if lat is not None and not -90 <= lat <= 90:
            self.add_error('latitude', 'Latitude harus antara -90 dan 90.')
        if lng is not None and not -180 <= lng <= 180:
            self.add_error('longitude', 'Longitude harus antara -180 dan 180.')
        return cleaned

import json
from datetime import timedelta

from django.contrib import messages
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .forms import LaporanWargaForm
from .models import KontakDarurat, Hotspot, LaporanWarga, PROVINSI_CHOICES, STATUS_LAPORAN


def _hotspot_dict(h):
    return {
        'id': h.id,
        'provinsi': h.provinsi,
        'provinsi_display': h.get_provinsi_display(),
        'lokasi_deskripsi': h.lokasi_deskripsi,
        'latitude': h.latitude,
        'longitude': h.longitude,
        'tingkat_kepercayaan': h.tingkat_kepercayaan,
        'status': h.status,
        'status_display': h.get_status_display(),
        'waktu_terdeteksi': h.waktu_terdeteksi.strftime('%Y-%m-%d %H:%M'),
    }


def _laporan_dict(l, include_reporter=False):
    data = {
        'id': l.id,
        'judul': l.judul,
        'provinsi': l.provinsi,
        'provinsi_display': l.get_provinsi_display(),
        'latitude': l.latitude,
        'longitude': l.longitude,
        'deskripsi': l.deskripsi,
        'status': l.status,
        'status_display': l.get_status_display(),
        'created_at': l.created_at.strftime('%Y-%m-%d %H:%M'),
        'foto_url': l.foto.url if l.foto else None,
        'detail_url': reverse('tracker:laporan_detail', args=[l.id]),
    }
    if include_reporter:
        data['pelapor_nama'] = l.pelapor_nama
    return data


def _apply_hotspot_filters(request, qs):
    provinsi = request.GET.get('provinsi', '')
    if provinsi in dict(PROVINSI_CHOICES):
        qs = qs.filter(provinsi=provinsi)
    status = request.GET.get('status', '')
    if status in ('SIAGA', 'AWAS'):
        qs = qs.filter(status=status)
    return qs


# ---------------------------------------------------------------------------
# Halaman Publik
# ---------------------------------------------------------------------------

def dashboard(request):
    hotspots = Hotspot.objects.all()
    now = timezone.now()

    per_provinsi = dict(
        hotspots.values('provinsi').annotate(total=Count('id')).values_list('provinsi', 'total')
    )
    provinsi_stats = [
        {'kode': k, 'nama': v, 'total': per_provinsi.get(k, 0)}
        for k, v in PROVINSI_CHOICES
    ]

    laporan_publik = LaporanWarga.objects.exclude(status='PENDING')[:6]

    context = {
        'total_hotspots': hotspots.count(),
        'hotspot_awas': hotspots.filter(status='AWAS').count(),
        'hotspot_24jam': hotspots.filter(waktu_terdeteksi__gte=now - timedelta(hours=24)).count(),
        'total_laporan': LaporanWarga.objects.count(),
        'laporan_publik': laporan_publik,
        'kontak_list': KontakDarurat.objects.all(),
        'provinsi_stats': provinsi_stats,
        'provinsi_choices': PROVINSI_CHOICES,
    }
    return render(request, 'tracker/index.html', context)


def laporan_list(request):
    qs = LaporanWarga.objects.exclude(status='PENDING')
    provinsi = request.GET.get('provinsi', '')
    if provinsi in dict(PROVINSI_CHOICES):
        qs = qs.filter(provinsi=provinsi)
    context = {
        'laporan_list': qs,
        'filter_provinsi': provinsi,
        'provinsi_choices': PROVINSI_CHOICES,
    }
    return render(request, 'tracker/laporan_list.html', context)


def laporan_create(request):
    if request.method == 'POST':
        form = LaporanWargaForm(request.POST, request.FILES)
        if form.is_valid():
            laporan = form.save()
            messages.success(request, 'Laporan berhasil dikirim dan menunggu verifikasi admin.')
            return redirect('tracker:laporan_success', pk=laporan.pk)
    else:
        form = LaporanWargaForm()
    return render(request, 'tracker/laporan_form.html', {'form': form})


def laporan_success(request, pk):
    laporan = get_object_or_404(LaporanWarga, pk=pk)
    return render(request, 'tracker/laporan_success.html', {'laporan': laporan})


def laporan_detail(request, pk):
    laporan = get_object_or_404(LaporanWarga.objects.exclude(status='PENDING'), pk=pk)
    return render(request, 'tracker/laporan_detail.html', {'laporan': laporan})


def kontak_page(request):
    kontak_list = KontakDarurat.objects.all()
    grouped = []
    for kode, nama in PROVINSI_CHOICES:
        items = [k for k in kontak_list if k.provinsi == kode]
        if items:
            grouped.append({'kode': kode, 'nama': nama, 'items': items})
    return render(request, 'tracker/kontak.html', {'provinsi_groups': grouped})


# ---------------------------------------------------------------------------
# API JSON
# ---------------------------------------------------------------------------

@require_GET
def api_hotspots(request):
    qs = _apply_hotspot_filters(request, Hotspot.objects.all())
    data = [_hotspot_dict(h) for h in qs]
    return JsonResponse({'count': len(data), 'hotspots': data})


@require_GET
def api_laporan(request):
    qs = LaporanWarga.objects.exclude(status='PENDING')
    provinsi = request.GET.get('provinsi', '')
    if provinsi in dict(PROVINSI_CHOICES):
        qs = qs.filter(provinsi=provinsi)
    status = request.GET.get('status', '')
    if status in dict(STATUS_LAPORAN):
        qs = qs.filter(status=status)
    data = [_laporan_dict(l) for l in qs]
    return JsonResponse({'count': len(data), 'laporan': data})


@require_GET
def api_kontak(request):
    qs = KontakDarurat.objects.all()
    provinsi = request.GET.get('provinsi', '')
    if provinsi in dict(PROVINSI_CHOICES):
        qs = qs.filter(provinsi=provinsi)
    data = [
        {
            'id': k.id,
            'nama_instansi': k.nama_instansi,
            'provinsi': k.provinsi,
            'provinsi_display': k.get_provinsi_display(),
            'nomor_telepon': k.nomor_telepon,
            'alamat': k.alamat or '',
        }
        for k in qs
    ]
    return JsonResponse({'count': len(data), 'kontak': data})


# ---------------------------------------------------------------------------
# Ekspor GeoJSON
# ---------------------------------------------------------------------------

def _geojson_response(features, filename):
    fc = {'type': 'FeatureCollection', 'features': features}
    resp = HttpResponse(json.dumps(fc, indent=2), content_type='application/geo+json')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


@require_GET
def export_hotspots_geojson(request):
    qs = _apply_hotspot_filters(request, Hotspot.objects.all())
    features = [
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [h.longitude, h.latitude]},
            'properties': _hotspot_dict(h),
        }
        for h in qs
    ]
    return _geojson_response(features, 'hotspots_kalimantan.geojson')


@require_GET
def export_laporan_geojson(request):
    qs = LaporanWarga.objects.exclude(status='PENDING').exclude(latitude=None).exclude(longitude=None)
    features = [
        {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [l.longitude, l.latitude]},
            'properties': _laporan_dict(l, include_reporter=True),
        }
        for l in qs
    ]
    return _geojson_response(features, 'laporan_warga_kalimantan.geojson')

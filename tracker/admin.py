from django.contrib import admin
from django.utils.html import format_html

from .models import Hotspot, KontakDarurat, LaporanWarga


@admin.action(description='Setujui & tampilkan di publik (VERIFIED)')
def approve_laporan(modeladmin, request, queryset):
    updated = queryset.update(status='VERIFIED')
    modeladmin.message_user(request, f'{updated} laporan berhasil diverifikasi.')


@admin.action(description='Tandai sedang ditangani (HANDLED)')
def mark_handled(modeladmin, request, queryset):
    updated = queryset.update(status='HANDLED')
    modeladmin.message_user(request, f'{updated} laporan ditandai sedang ditangani.')


@admin.action(description='Tandai padam / selesai (RESOLVED)')
def mark_resolved(modeladmin, request, queryset):
    updated = queryset.update(status='RESOLVED')
    modeladmin.message_user(request, f'{updated} laporan ditandai padam / selesai.')


@admin.register(Hotspot)
class HotspotAdmin(admin.ModelAdmin):
    list_display = ('provinsi', 'lokasi_deskripsi', 'tingkat_kepercayaan', 'status', 'waktu_terdeteksi')
    list_filter = ('provinsi', 'status')
    search_fields = ('lokasi_deskripsi',)
    list_select_related = False
    date_hierarchy = 'waktu_terdeteksi'


@admin.register(LaporanWarga)
class LaporanWargaAdmin(admin.ModelAdmin):
    list_display = ('id', 'judul', 'pelapor_nama', 'provinsi', 'status_badge', 'created_at', 'foto_thumb')
    list_filter = ('status', 'provinsi', 'created_at')
    search_fields = ('judul', 'pelapor_nama', 'deskripsi', 'pelapor_kontak')
    actions = [approve_laporan, mark_handled, mark_resolved]
    readonly_fields = ('created_at', 'foto_preview')
    fieldsets = (
        ('Laporan', {
            'fields': ('judul', 'deskripsi', 'foto', 'foto_preview'),
        }),
        ('Pelapor', {
            'fields': ('pelapor_nama', 'pelapor_kontak'),
        }),
        ('Lokasi', {
            'fields': ('provinsi', 'latitude', 'longitude'),
        }),
        ('Status', {
            'fields': ('status', 'created_at'),
        }),
    )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f59e0b',
            'VERIFIED': '#f97316',
            'HANDLED': '#0ea5e9',
            'RESOLVED': '#10b981',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:6px;font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description='Foto')
    def foto_thumb(self, obj):
        if obj.foto:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:4px;" />', obj.foto.url
            )
        return '-'

    @admin.display(description='Pratinjau Foto')
    def foto_preview(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-height:240px;border-radius:8px;" />', obj.foto.url)
        return 'Tidak ada foto'


@admin.register(KontakDarurat)
class KontakDaruratAdmin(admin.ModelAdmin):
    list_display = ('nama_instansi', 'provinsi', 'nomor_telepon')
    list_filter = ('provinsi',)
    search_fields = ('nama_instansi', 'nomor_telepon')

from django.urls import path

from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('laporan/', views.laporan_list, name='laporan_list'),
    path('laporan/baru/', views.laporan_create, name='laporan_create'),
    path('laporan/<int:pk>/', views.laporan_detail, name='laporan_detail'),
    path('laporan/<int:pk>/sukses/', views.laporan_success, name='laporan_success'),
    path('kontak/', views.kontak_page, name='kontak'),
    # API JSON
    path('api/hotspots/', views.api_hotspots, name='api_hotspots'),
    path('api/laporan/', views.api_laporan, name='api_laporan'),
    path('api/kontak/', views.api_kontak, name='api_kontak'),
    # Ekspor GeoJSON
    path('api/export/hotspots.geojson', views.export_hotspots_geojson, name='export_hotspots'),
    path('api/export/laporan.geojson', views.export_laporan_geojson, name='export_laporan'),
]

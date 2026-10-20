/**
 * Helper dasar peta: tile Google Maps (tampilan seperti Google Maps,
 * tanpa API key) dengan fallback otomatis Esri → OpenStreetMap
 * jika terjadi error tile (mis. diblokir jaringan).
 *
 * Pakai:  const map = L.map('map').setView([...], zoom);
 *         tambahPetaDasar(map);
 */
window.tambahPetaDasar = function (map) {
    const sumber = [
        function () {
            return L.tileLayer('https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
                maxZoom: 20,
                subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
                attribution: '© Google Maps',
            });
        },
        function () {
            return L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
                maxZoom: 19,
                attribution: '© Esri, HERE, Garmin, FAO, NOAA, USGS',
            });
        },
        function () {
            return L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 18,
                attribution: '© OpenStreetMap contributors',
            });
        },
    ];

    let index = 0;

    function cobaBerikutnya() {
        if (index >= sumber.length) return;
        const buatLayer = sumber[index++];
        const layer = buatLayer();
        let gagal = 0;
        layer.on('tileerror', function () {
            gagal += 1;
            if (gagal >= 3) {
                map.removeLayer(layer);
                cobaBerikutnya();
            }
        });
        layer.addTo(map);
    }

    cobaBerikutnya();
};

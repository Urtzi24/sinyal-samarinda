/**
 * Nama kecamatan di atas peta.
 *
 * Tanpa nama daerah, peta ini cuma bentuk berwarna: orang tahu ada daerah yang
 * bagus, tapi tidak tahu daerah mana. Pencarian alamat sengaja ditunda, jadi
 * nama kecamatan inilah satu-satunya cara orang menemukan tempatnya sendiri.
 *
 * Labelnya digambar sebagai elemen HTML biasa, BUKAN lapisan simbol MapLibre.
 * Lapisan simbol menuntut berkas huruf peta (glyph) yang lazimnya diambil dari
 * layanan luar — dan itu dilarang. Sebagai elemen HTML, labelnya memakai huruf
 * yang sudah disimpan sendiri, tanpa satu pun permintaan ke pihak ketiga.
 */

import * as maplibregl from "maplibre-gl";

const DISTRICTS_URL = "/ubin/kecamatan.json";

/** Di bawah zoom ini labelnya disembunyikan supaya tidak saling menumpuk. */
const MIN_LABEL_ZOOM = 10.5;

type District = { nama: string; lon: number; lat: number };

export async function addDistrictLabels(map: maplibregl.Map): Promise<void> {
  let kecamatan: District[];
  try {
    const respons = await fetch(DISTRICTS_URL);
    if (!respons.ok) throw new Error(`HTTP ${respons.status}`);
    kecamatan = await respons.json();
  } catch (galat) {
    // Peta tanpa label masih terbaca; peta yang gagal termuat tidak.
    console.error("[peta] nama kecamatan gagal dimuat:", galat);
    return;
  }

  const penanda = kecamatan.map((k) => {
    const elemen = document.createElement("span");
    elemen.className = "district-label";
    elemen.textContent = k.nama;
    return new maplibregl.Marker({ element: elemen })
      .setLngLat([k.lon, k.lat])
      .addTo(map);
  });

  const perbaruiTampak = () => {
    const tampak = map.getZoom() >= MIN_LABEL_ZOOM;
    for (const p of penanda) {
      p.getElement().style.display = tampak ? "" : "none";
    }
  };

  perbaruiTampak();
  map.on("zoom", perbaruiTampak);
}

/**
 * Peta 3D: bentang alam Samarinda dengan lapisan perkiraan sinyal di atasnya.
 */

import * as maplibregl from "maplibre-gl";
import type { RequestParameters } from "maplibre-gl";
// Vite yang menentukan alamat akhirnya, jadi benar di pengembangan maupun
// hasil bangun.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { PMTiles, Protocol } from "pmtiles";

/**
 * Tunjuk berkas pekerja latar MapLibre secara eksplisit.
 *
 * MapLibre mengurai data vektor — garis, lingkaran, poligon — di pekerja latar.
 * Raster tidak. Waktu pekerjanya gagal dimuat, gejalanya menyesatkan: peta
 * tetap tampil karena lapisan rasternya hidup, sementara SELURUH lapisan vektor
 * diam tanpa satu pun galat. Sumbernya bahkan mengaku "termuat" padahal tidak
 * pernah meminta satu ubin pun.
 *
 * Vite sempat memperingatkan `maplibre-gl-worker.mjs` tidak ada, dan peringatan
 * itu terlihat tidak berbahaya justru karena rasternya tetap jalan.
 */
maplibregl.setWorkerUrl(workerUrl);
import { tingkatAwal, type Tingkat } from "./kualitas";
import { INK, INK_MUTED, SURFACE } from "./palette";
import { colorizePng, decodeDbm } from "./tile";

export const OPERATORS = ["telkomsel", "ioh", "xlsmart"] as const;
export type OperatorId = (typeof OPERATORS)[number];

export const OPERATOR_NAMES: Record<OperatorId, string> = {
  telkomsel: "Telkomsel",
  ioh: "Indosat Ooredoo Hutchison",
  xlsmart: "XLSmart",
};

const TILE_BASE = "/ubin";
// HARUS sama dengan DEFAULT_MIN_ZOOM dan DEFAULT_MAX_ZOOM di dapur/run.py.
// Alasannya ada di sana: kalau peta minta lebih dalam daripada yang dibuat
// dapur, zoom terdalam jadi kosong tanpa satu pun pesan galat.
const MIN_ZOOM = 10;
const MAX_ZOOM = 15;

/** Ubin kota (gedung dan jalan) tersedia sampai zoom ini. */
const CITY_MAX_ZOOM = 16;

/**
 * Tinggi satu lantai dalam meter, dipakai untuk gedung yang tidak menyebutkan
 * tingginya.
 *
 * Dari 241 ribu gedung Samarinda di OpenStreetMap, cuma 57 punya tinggi
 * sebenarnya dan 2.413 punya jumlah lantai. Sisanya — lebih dari 99% —
 * ditegakkan dengan angka ini.
 *
 * Itu asumsi, bukan pengukuran, dan halaman WAJIB menyatakannya. Gedungnya ada
 * untuk membuat kota terlihat seperti kota, bukan untuk dipercaya tingginya.
 * Angka 3,5 m adalah tinggi lantai bangunan biasa.
 */
const FLOOR_HEIGHT_M = 3.5;
const DEFAULT_FLOORS = 2;

/** Tengah Kota Samarinda, dari kotak batas relasi OpenStreetMap. */
const CENTER: [number, number] = [117.1761, -0.5156];

/**
 * Pelebihan tinggi bentang alam.
 *
 * Samarinda hampir datar: separuh kota di bawah 22 m, dan beda tinggi 327 m
 * tersebar sepanjang 27 km — kemiringan rata-rata cuma 1,2%. Pada skala
 * sebenarnya, bukitnya tidak terlihat sama sekali walau peta dimiringkan.
 *
 * Sempat disetel empat kali, dan itu terlalu banyak: pelebihan sebesar itu ikut
 * menguatkan pembulatan di data ketinggian, sehingga lereng landai tergambar
 * berundak seperti terasering — jurang palsu yang tidak ada di lapangan.
 *
 * Sejak gedung 3D berdiri, kesan tinggi sudah datang dari gedungnya, jadi
 * bentang alamnya tidak perlu dilebihkan sebanyak itu lagi.
 *
 * Yang tetap dijaga REDUP adalah WARNANYA, bukan bentuknya. PRD bagian 10
 * mewajibkan warna sinyal jadi satu-satunya hal pekat di layar; bayangan
 * bukitnya tetap abu tipis.
 */
const TERRAIN_EXAGGERATION = 1.8;

/**
 * Lapisan hiasan yang dilepas saat kerincian diturunkan — FR-018.
 *
 * Namanya ditulis sekali di sini, lalu dipakai baik oleh definisi gayanya
 * maupun oleh `setQuality`. Kalau ditulis dua kali, salah ketik di salah satu
 * tempat membuat penurunan kerincian diam-diam tidak melepas apa-apa: peta
 * tetap tersendat, dan tidak ada satu pun galat yang memberi tahu.
 */
const LAPISAN_HIASAN = {
  bayanganBukit: "bayangan-bukit",
  gedung3d: "gedung-3d",
} as const;

const pmtilesPerOperator = new Map<string, PMTiles>();

function archiveFor(operator: OperatorId): PMTiles {
  let arsip = pmtilesPerOperator.get(operator);
  if (!arsip) {
    arsip = new PMTiles(`${TILE_BASE}/sinyal-${operator}.pmtiles`);
    pmtilesPerOperator.set(operator, arsip);
  }
  return arsip;
}

/**
 * Protokol sendiri untuk ubin sinyal: baca dari arsip, warnai, serahkan ke
 * MapLibre. Alamatnya berbentuk `sinyal://<operator>/<z>/<x>/<y>`.
 */
function registerSignalProtocol(): void {
  maplibregl.addProtocol("sinyal", async (params: RequestParameters) => {
    const bagian = params.url.replace("sinyal://", "").split("/");
    const operator = bagian[0] as OperatorId;
    const z = Number(bagian[1]);
    const x = Number(bagian[2]);
    const y = Number(bagian[3]);

    const ubin = await archiveFor(operator).getZxy(z, x, y);
    if (!ubin?.data) return { data: null };

    return { data: await colorizePng(ubin.data) };
  });
}

/** Baca nilai mentah satu titik, langsung dari arsip. */
export async function sampleAt(
  operator: OperatorId,
  lng: number,
  lat: number,
  zoom: number,
): Promise<{ dbm: number; adequate: boolean; insideCity: boolean } | null> {
  const z = Math.min(Math.max(Math.round(zoom), MIN_ZOOM), MAX_ZOOM);
  const n = 2 ** z;
  const xf = ((lng + 180) / 360) * n;
  const latRad = (lat * Math.PI) / 180;
  const yf = ((1 - Math.asinh(Math.tan(latRad)) / Math.PI) / 2) * n;

  const ubin = await archiveFor(operator).getZxy(z, Math.floor(xf), Math.floor(yf));
  if (!ubin?.data) return null;

  const gambar = await createImageBitmap(new Blob([ubin.data]));
  const kanvas = new OffscreenCanvas(gambar.width, gambar.height);
  const konteks = kanvas.getContext("2d", { willReadFrequently: true });
  if (!konteks) return null;
  konteks.drawImage(gambar, 0, 0);
  gambar.close();

  const px = Math.min(Math.floor((xf % 1) * kanvas.width), kanvas.width - 1);
  const py = Math.min(Math.floor((yf % 1) * kanvas.height), kanvas.height - 1);
  const piksel = konteks.getImageData(px, py, 1, 1).data;

  return {
    dbm: decodeDbm(piksel[0] ?? 0, piksel[1] ?? 0),
    adequate: (piksel[2] ?? 0) !== 0,
    insideCity: (piksel[3] ?? 0) !== 0,
  };
}

/**
 * Sumber dan lapisan sinyal untuk ketiga operator.
 *
 * Semuanya dideklarasikan di GAYA AWAL, bukan ditambahkan setelah peta termuat.
 * Menambahkannya belakangan sempat membuat peta tampil kosong sama sekali:
 * peristiwa `load` baru menyala setelah seluruh sumber awal tuntas, dan sumber
 * ketinggian di sini cuma menutupi Samarinda — permintaan ubin di luar kota
 * tidak pernah selesai, jadi `load` tidak pernah menyala, lapisan sinyal tidak
 * pernah dipasang, dan tidak ada satu pun pesan galat yang menjelaskannya.
 *
 * Dideklarasikan di muka, tidak ada yang perlu ditunggu.
 */
function signalSources(): Record<string, maplibregl.SourceSpecification> {
  return Object.fromEntries(
    OPERATORS.map((operator) => [
      `sinyal-${operator}`,
      {
        type: "raster",
        tiles: [`sinyal://${operator}/{z}/{x}/{y}`],
        tileSize: 256,
        minzoom: MIN_ZOOM,
        maxzoom: MAX_ZOOM,
      } as maplibregl.SourceSpecification,
    ]),
  );
}

/**
 * Jalan kota dari ubin vektor, satu lapisan per kelas.
 *
 * Urutannya dari kecil ke besar supaya jalan besar tergambar di atas gang, dan
 * ketebalannya menaik mengikuti kelasnya. Semuanya teredam — kerangka untuk
 * mengenali tempat, bukan hal yang harus dilihat lebih dulu.
 */
function cityRoadLayers(): maplibregl.LayerSpecification[] {
  // [nama kelas, lebar di zoom 13, lebar di zoom 17, kepekatan]
  //
  // Kepekatannya BERTINGKAT, tidak seragam. Waktu semua kelas sama pekat, gang
  // kecil sama menonjolnya dengan jalan utama — petanya jadi ramai tanpa
  // menolong. Jalan raya harus terbaca lebih dulu; gang cukup jadi tekstur
  // halus yang menunjukkan mana yang padat permukiman.
  const kelas: Array<[string, number, number, number]> = [
    ["path", 0.3, 1.2, 0.22],
    ["footway", 0.3, 1.2, 0.22],
    ["service", 0.4, 1.6, 0.28],
    ["living_street", 0.5, 2, 0.32],
    ["unclassified", 0.6, 2.4, 0.38],
    ["residential", 0.7, 3, 0.45],
    ["tertiary", 1.1, 4.5, 0.62],
    ["secondary", 1.5, 6, 0.75],
    ["primary", 1.9, 7.5, 0.85],
    ["trunk", 2.2, 9, 0.92],
    ["motorway", 2.6, 11, 1.0],
  ];

  return kelas.map(([nama, tipis, tebal, pekat]) => ({
    id: `kota-jalan-${nama}`,
    type: "line",
    source: "kota",
    "source-layer": `jalan_${nama}`,
    layout: { "line-cap": "round", "line-join": "round" },
    paint: {
      // Jalan digambar TERANG di atas warna sinyal yang gelap, bukan gelap di
      // atas gelap. Versi pertama memakai tinta gelap dengan kepekatan 0,35 —
      // hampir tidak terlihat di atas teal pekat, dan jalan yang tidak terlihat
      // sama saja dengan tidak ada.
      "line-color": SURFACE,
      "line-opacity": ["interpolate", ["linear"], ["zoom"], 12, pekat * 0.6, 16, pekat],
      "line-width": ["interpolate", ["linear"], ["zoom"], 13, tipis, 17, tebal],
    },
  })) as maplibregl.LayerSpecification[];
}

function signalLayers(active: OperatorId): maplibregl.LayerSpecification[] {
  return OPERATORS.map((operator) => ({
    id: `lapisan-${operator}`,
    type: "raster",
    source: `sinyal-${operator}`,
    layout: { visibility: operator === active ? "visible" : "none" },
    paint: { "raster-opacity": 1, "raster-resampling": "nearest" },
  })) as maplibregl.LayerSpecification[];
}

export function createMap(container: HTMLElement, active: OperatorId): maplibregl.Map {
  maplibregl.addProtocol("pmtiles", new Protocol().tile);
  registerSignalProtocol();

  const map = new maplibregl.Map({
    container,
    center: CENTER,
    zoom: 11,
    pitch: 45,
    maxPitch: 75,
    minZoom: MIN_ZOOM - 1,
    maxZoom: MAX_ZOOM + 2,
    attributionControl: false,
    style: {
      version: 8,
      // Tidak ada kunci `glyphs` sama sekali: huruf peta tidak dipanggil dari
      // layanan luar, dan selama belum ada label bawaan MapLibre, menuliskannya
      // kosong justru ditolak sebagai gaya tidak sah.
      sources: {
        // Templat ubin ditulis eksplisit, bukan lewat `url`. Bentuk TileJSON
        // yang dikembalikan protokol pmtiles ternyata tidak membuat MapLibre
        // meminta satu ubin pun untuk sumber raster-dem — kepalanya terbaca,
        // lalu berhenti di situ tanpa pesan galat.
        ketinggian: {
          type: "raster-dem",
          tiles: [`pmtiles://${TILE_BASE}/ketinggian.pmtiles/{z}/{x}/{y}`],
          tileSize: 256,
          minzoom: MIN_ZOOM,
          maxzoom: MAX_ZOOM,
          encoding: "terrarium",
        },
        ...signalSources(),
        gedung: { type: "geojson", data: `${TILE_BASE}/gedung-pemerintahan.geojson` },
        // Kembali ke protokol pmtiles: satu berkas arsip, tanpa perlu pelayan
        // yang memotongnya. Inilah yang membuat peta ini bisa diunggah ke
        // tempat statis mana pun.
        //
        // Sempat diganti alamat HTTP biasa karena lewat `pmtiles://` nol fitur
        // termuat — tapi itu ternyata gejala dari pekerja latar MapLibre yang
        // tidak pernah hidup, bukan salah protokolnya.
        kota: {
          type: "vector",
          tiles: [`pmtiles://${TILE_BASE}/kota.pmtiles/{z}/{x}/{y}`],
          minzoom: MIN_ZOOM,
          maxzoom: CITY_MAX_ZOOM,
        },
      },
      layers: [
        { id: "latar", type: "background", paint: { "background-color": SURFACE } },
        ...signalLayers(active),
        // Bayangan bukit ditaruh DI ATAS warna sinyal, bukan di bawahnya.
        //
        // Di bawah, ia tertutup hampir seluruhnya — lapisan sinyal menutup 84%
        // dan reliefnya hilang. Di atas, ia menggelapkan lereng yang menghadap
        // menjauh dari cahaya, sehingga warna sinyalnya terbaca menempel di
        // permukaan tanah, bukan melayang di atasnya.
        {
          id: LAPISAN_HIASAN.bayanganBukit,
          type: "hillshade",
          source: "ketinggian",
          paint: {
            "hillshade-shadow-color": INK_MUTED,
            "hillshade-highlight-color": SURFACE,
            "hillshade-accent-color": INK_MUTED,
            // Lemah, dan itu disengaja.
            //
            // Copernicus DEM punya derau beberapa meter. Di tanah selandai
            // Samarinda — kemiringan rata-rata 1,2% — derau itu setara dengan
            // reliefnya sendiri, sehingga bayangan yang kuat menghasilkan
            // bintik kasar, bukan bentuk bukit. Pada 0,45 seluruh peta terlihat
            // berpasir dan mudah dikira kegagalan kerincian.
            "hillshade-exaggeration": 0.12,
          },
        },
        // Sungai, jalan, dan gedung digambar DI ATAS warna sinyal.
        //
        // Di bawah, semuanya tertutup dan tidak menolong siapa pun. Di atas,
        // mereka jadi kerangka yang membuat orang mengenali kotanya sendiri —
        // dan itu satu-satunya cara menemukan tempat tinggal, karena pencarian
        // alamat sengaja ditunda.
        //
        // Semuanya teredam supaya warna sinyal tetap yang paling pekat di
        // layar, sesuai PRD bagian 10.
        {
          id: "sungai",
          type: "line",
          source: "kota",
          "source-layer": "jalan_sungai",
          layout: { "line-cap": "round", "line-join": "round" },
          paint: {
            // Sungai Mahakam membelah kota dan jadi patokan paling dikenali.
            // Digambar lebih tebal dan lebih pekat daripada jalan mana pun.
            "line-color": SURFACE,
            "line-opacity": 0.8,
            "line-width": ["interpolate", ["linear"], ["zoom"], 10, 3, 16, 22],
          },
        },
        ...cityRoadLayers(),
        // Gedung 3D.
        //
        // PERINGATAN: lebih dari 99% tingginya diasumsikan — cuma 57 dari 241
        // ribu gedung Samarinda punya tinggi sebenarnya di OpenStreetMap.
        // Gedung ini ada supaya kotanya terlihat seperti kota, bukan supaya
        // tingginya dipercaya. Halaman menyatakannya di bagian batasan.
        {
          id: LAPISAN_HIASAN.gedung3d,
          type: "fill-extrusion",
          source: "kota",
          "source-layer": "gedung",
          minzoom: 14,
          paint: {
            // Diredam sedikit dari putih penuh: gedung tidak boleh jadi hal
            // paling terang di layar, karena yang harus paling menonjol adalah
            // warna sinyal — itu aturan PRD bagian 10.
            "fill-extrusion-color": "#d8d3c8",
            "fill-extrusion-opacity": 0.72,
            "fill-extrusion-base": 0,
            "fill-extrusion-height": [
              "*",
              ["coalesce", ["get", "lantai"], DEFAULT_FLOORS],
              FLOOR_HEIGHT_M,
            ],
          },
        },
        // Gedung pemerintahan sebagai patokan tempat.
        //
        // Titik, bukan bentuk bangunan: pada zoom kota satu gedung cuma
        // beberapa piksel, jadi bentuknya tidak terbaca sementara datanya
        // sepuluh kali lebih berat.
        //
        // Ini TIDAK membatalkan keputusan "bentang alam 3D, bukan gedung" di
        // PRD bagian 14 — gedungnya tidak dibentuk 3D dan tidak ikut
        // perhitungan propagasi. Perannya patokan, bukan penghalang sinyal.
        {
          id: "gedung-pemerintahan",
          type: "circle",
          source: "gedung",
          paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 2.5, 16, 6],
            "circle-color": SURFACE,
            "circle-stroke-color": INK,
            "circle-stroke-width": 1,
            "circle-opacity": 0.9,
          },
        },
      ],
    },
  });

  // Peta yang gagal diam-diam adalah kegagalan terburuk di sini: halamannya
  // tetap tampil rapi, cuma kosong, dan tidak ada satu pun petunjuk kenapa.
  map.on("error", (peristiwa) => {
    const pesan = peristiwa?.error?.message ?? String(peristiwa?.error ?? peristiwa);
    console.error("[peta]", pesan);
  });

  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
  map.addControl(
    new maplibregl.AttributionControl({
      customAttribution:
        "Data pemancar OpenCelliD (CC BY-SA) · Ketinggian Copernicus DEM · Batas OpenStreetMap",
    }),
    "bottom-right",
  );

  // Nama gedung muncul saat tetikus menyentuhnya. Tidak dipasang sebagai label
  // tetap: 307 nama sekaligus menutupi datanya sendiri. Tidak dipasang di klik
  // juga, karena klik sudah dipakai membaca nilai sinyal.
  const namaGedung = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
    offset: 8,
  });

  map.on("mouseenter", "gedung-pemerintahan", (peristiwa) => {
    const fitur = peristiwa.features?.[0];
    if (!fitur || fitur.geometry.type !== "Point") return;
    map.getCanvas().style.cursor = "pointer";
    namaGedung
      .setLngLat(fitur.geometry.coordinates as [number, number])
      .setText(String(fitur.properties?.nama ?? ""))
      .addTo(map);
  });

  map.on("mouseleave", "gedung-pemerintahan", () => {
    map.getCanvas().style.cursor = "";
    namaGedung.remove();
  });

  // Bentang alam 3D dinyalakan setelah gayanya terurai. Dipisah dari deklarasi
  // gaya karena `setTerrain` menuntut sumber ketinggiannya sudah terdaftar.
  //
  // Pada perangkat yang keterangannya sudah menyatakan tidak sanggup, ia tidak
  // pernah dinyalakan sama sekali — bukan dinyalakan lalu dimatikan setelah
  // tabnya kepayahan.
  map.once("styledata", () => setQuality(map, tingkatAwal()));

  return map;
}

/**
 * Pasang tingkat kerincian tampilan — FR-018.
 *
 * Yang dilepas di tingkat ringan cuma hiasan: bentang alam 3D, bayangan bukit,
 * dan gedung ber-ekstrusi. Warna sinyal, jalan, batas kota, dan nama kecamatan
 * tetap ada, jadi peta yang tersisa masih menjawab pertanyaan yang jadi alasan
 * ia dibuat.
 *
 * Titik gedung pemerintahan ikut tinggal: ia lingkaran, bukan bentuk terdorong
 * naik, dan patokan tempat justru makin dibutuhkan begitu reliefnya hilang.
 */
export function setQuality(map: maplibregl.Map, tingkat: Tingkat): void {
  const penuh = tingkat === "penuh";

  try {
    map.setTerrain(penuh ? { source: "ketinggian", exaggeration: TERRAIN_EXAGGERATION } : null);
  } catch (galat) {
    // Peta tanpa relief masih berguna; peta yang gagal termuat tidak.
    console.error("[peta] bentang alam 3D gagal diatur:", galat);
  }

  for (const id of Object.values(LAPISAN_HIASAN)) {
    if (map.getLayer(id)) {
      map.setLayoutProperty(id, "visibility", penuh ? "visible" : "none");
    }
  }
}

/**
 * Tampilkan satu operator, sembunyikan sisanya.
 *
 * Berganti operator TIDAK boleh memuat ulang halaman atau menggeser peta —
 * perbandingan harus satu ketukan, dan itu inti kegunaannya.
 */
export function showOperator(map: maplibregl.Map, operator: OperatorId): void {
  for (const lain of OPERATORS) {
    if (!map.getLayer(`lapisan-${lain}`)) continue;
    map.setLayoutProperty(
      `lapisan-${lain}`,
      "visibility",
      lain === operator ? "visible" : "none",
    );
  }
}

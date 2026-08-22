/**
 * Titik masuk etalase.
 */

import "maplibre-gl/dist/maplibre-gl.css";
import "./style.css";

import type * as maplibregl from "maplibre-gl";

import { awasiKinerja } from "./kualitas";
import { addDistrictLabels } from "./labels";
import { renderLegend } from "./legend";
import { createMap, sampleAt, setQuality, showOperator, type OperatorId } from "./map";
import { renderOperators } from "./operators";
import { renderReadout, type Sample } from "./readout";
import { loadSummary, renderTable } from "./table";

const OPERATOR_AWAL: OperatorId = "telkomsel";

const wadahPeta = document.querySelector<HTMLElement>("#peta");
const wadahOperator = document.querySelector<HTMLElement>("#pemilih-operator");
const wadahWarna = document.querySelector<HTMLElement>("#keterangan-warna");
const wadahTitik = document.querySelector<HTMLElement>("#titik-terpilih");
const tombolBatasan = document.querySelector<HTMLButtonElement>("#tombol-batasan");
const wadahBatasan = document.querySelector<HTMLElement>("#batasan");
const tombolTabel = document.querySelector<HTMLButtonElement>("#tombol-tabel");
const tutupTabel = document.querySelector<HTMLButtonElement>("#tutup-tabel");
const jendelaTabel = document.querySelector<HTMLDialogElement>("#tabel-per-kecamatan");
const isiTabel = document.querySelector<HTMLElement>("#isi-tabel");

if (
  !wadahPeta ||
  !wadahOperator ||
  !wadahWarna ||
  !wadahTitik ||
  !tombolBatasan ||
  !wadahBatasan ||
  !tombolTabel ||
  !tutupTabel ||
  !jendelaTabel ||
  !isiTabel
) {
  throw new Error("kerangka halaman tidak lengkap");
}

let operatorAktif: OperatorId = OPERATOR_AWAL;
let titikTerakhir: { lng: number; lat: number } | null = null;

const map = createMap(wadahPeta, operatorAktif);

renderLegend(wadahWarna);
renderOperators(wadahOperator, operatorAktif, (operator) => {
  operatorAktif = operator;
  showOperator(map, operator);
  void perbaruiTitik();
});

showOperator(map, operatorAktif);
void addDistrictLabels(map);

// Turunkan kerincian kalau petanya ternyata tersendat — FR-018.
//
// Dan katakan bahwa itu terjadi. Peta yang diam-diam kehilangan bentang alam
// 3D-nya terbaca seperti peta yang rusak; peta yang bilang kenapa terbaca
// seperti peta yang mengalah supaya tetap bisa dipakai.
awasiKinerja(() => {
  setQuality(map, "ringan");
  const kabar = document.createElement("p");
  kabar.className = "hud hud--kabar";
  kabar.setAttribute("role", "status");
  kabar.textContent =
    "Bentang alam 3D dimatikan supaya peta tetap lancar di perangkat ini. " +
    "Warna sinyalnya tidak berubah.";
  document.body.append(kabar);
  setTimeout(() => kabar.remove(), 9000);
});

async function perbaruiTitik(): Promise<void> {
  if (!titikTerakhir) return;
  const contoh: Sample = await sampleAt(
    operatorAktif,
    titikTerakhir.lng,
    titikTerakhir.lat,
    map.getZoom(),
  );
  renderReadout(wadahTitik!, operatorAktif, contoh);
}

map.on("click", (peristiwa: maplibregl.MapMouseEvent) => {
  titikTerakhir = { lng: peristiwa.lngLat.lng, lat: peristiwa.lngLat.lat };
  void perbaruiTitik();
});

// Batasan disembunyikan di balik satu tombol, bukan dihapus.
//
// FR-012 mewajibkannya terbaca di halaman peta itu sendiri. Tombolnya selalu
// terlihat dan namanya menyebut isinya, jadi tidak ada yang perlu dicari-cari —
// tapi ia tidak lagi memakan seperlima layar.
tombolBatasan.addEventListener("click", () => {
  const terbuka = wadahBatasan.hidden;
  wadahBatasan.hidden = !terbuka;
  tombolBatasan.setAttribute("aria-expanded", String(terbuka));
});

// Tabel per kecamatan — FR-013.
//
// Isinya diambil sekali saat pertama dibuka, bukan saat halaman dimuat: orang
// yang cuma melihat petanya tidak perlu ikut menunggu berkasnya turun. Kalau
// gagal, kegagalannya ditulis di tempat tabelnya seharusnya muncul — bukan cuma
// di konsol yang tidak dilihat siapa pun.
let tabelTerisi = false;

async function bukaTabel(): Promise<void> {
  jendelaTabel!.showModal();
  if (tabelTerisi) return;
  try {
    renderTable(isiTabel!, await loadSummary());
    tabelTerisi = true;
  } catch (galat) {
    isiTabel!.innerHTML =
      `<p class="tabel__galat">Tabelnya gagal dimuat: ${String(galat)}. ` +
      `Perkiraannya masih bisa dibaca dari peta.</p>`;
  }
}

tombolTabel.addEventListener("click", () => void bukaTabel());
tutupTabel.addEventListener("click", () => jendelaTabel.close());

// Menekan latar gelap di luar jendela juga menutup — tapi cuma latarnya.
// Tanpa pemeriksaan ini, menekan tabelnya sendiri ikut menutup jendela, karena
// peristiwanya menggelembung ke elemen dialog yang sama.
jendelaTabel.addEventListener("click", (peristiwa) => {
  if (peristiwa.target === jendelaTabel) jendelaTabel.close();
});

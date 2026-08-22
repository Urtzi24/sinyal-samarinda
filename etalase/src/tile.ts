/**
 * Pembacaan ubin sinyal dan pewarnaannya di peramban.
 *
 * Kontraknya di specs/001-signal-prediction-map/contracts/tile-format.md:
 *
 *     R, G : nilai 16 bit = (dBm + 140) * 10
 *     B    : 0 = data tidak memadai, 255 = memadai
 *     A    : 0 = di luar batas kota, 255 = di dalam
 *
 * Kenapa diwarnai di sini dan bukan di dapur: PRD mengunci keputusan menyimpan
 * NILAI di ubin, bukan warna jadi, supaya skema warnanya bisa diganti tanpa
 * menghitung ulang berjam-jam. MapLibre sendiri tidak bisa mewarnai raster
 * bernilai — properti `raster-color` itu milik Mapbox, tidak ada di MapLibre —
 * jadi pewarnaannya dikerjakan sendiri di sini.
 */

import { NO_DATA_COLOR, SIGNAL_STEPS, signalLevel } from "./palette";

const DBM_OFFSET = 140;
const DBM_SCALE = 10;

/** Lebar dan jarak arsir untuk wilayah tanpa data, dalam piksel. */
const HATCH_PERIOD = 8;
const HATCH_WIDTH = 3;

/** Kepekatan warna sinyal di atas bentang alam. */
const SIGNAL_ALPHA = 214;

export function decodeDbm(red: number, green: number): number {
  return ((red << 8) | green) / DBM_SCALE - DBM_OFFSET;
}

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

const STEP_RGB = SIGNAL_STEPS.map(hexToRgb);
const NO_DATA_RGB = hexToRgb(NO_DATA_COLOR);

/**
 * Warnai satu ubin di tempat.
 *
 * Urutan pemeriksaannya mengikuti kontrak dan tidak boleh ditukar: alfa lebih
 * dulu, lalu kanal biru, baru nilainya. Kalau nilai dibaca lebih dulu, wilayah
 * tanpa data akan tampil sebagai sinyal sangat lemah — dan itu tuduhan yang
 * salah terhadap operator yang cuma menaranya tidak terdaftar.
 */
export function colorizeTile(pixels: Uint8ClampedArray, width: number): void {
  const [nrR, nrG, nrB] = NO_DATA_RGB;
  const jumlahTingkat = STEP_RGB.length;

  for (let i = 0; i < pixels.length; i += 4) {
    if (pixels[i + 3] === 0) continue; // di luar batas kota

    const nomor = i / 4;
    const x = nomor % width;
    const y = (nomor / width) | 0;

    if (pixels[i + 2] === 0) {
      // Data tidak memadai. Arsir miring yang jadi pembeda utamanya — warnanya
      // saja terlalu dekat dengan tingkat sinyal terlemah untuk diandalkan.
      const diarsir = (x + y) % HATCH_PERIOD < HATCH_WIDTH;
      pixels[i] = nrR;
      pixels[i + 1] = nrG;
      pixels[i + 2] = nrB;
      pixels[i + 3] = diarsir ? SIGNAL_ALPHA : 60;
      continue;
    }

    const dbm = decodeDbm(pixels[i] as number, pixels[i + 1] as number);
    const tingkat = Math.min(signalLevel(dbm), jumlahTingkat - 1);
    const warna = STEP_RGB[tingkat] as readonly [number, number, number];
    pixels[i] = warna[0];
    pixels[i + 1] = warna[1];
    pixels[i + 2] = warna[2];
    pixels[i + 3] = SIGNAL_ALPHA;
  }
}

/** Ubah bita PNG jadi PNG lain yang sudah diwarnai. */
export async function colorizePng(bytes: ArrayBuffer): Promise<ArrayBuffer> {
  const gambar = await createImageBitmap(new Blob([bytes]));
  const kanvas = new OffscreenCanvas(gambar.width, gambar.height);
  const konteks = kanvas.getContext("2d", { willReadFrequently: true });
  if (!konteks) throw new Error("kanvas dua dimensi tidak tersedia");

  konteks.drawImage(gambar, 0, 0);
  gambar.close();

  const data = konteks.getImageData(0, 0, kanvas.width, kanvas.height);
  colorizeTile(data.data, kanvas.width);
  konteks.putImageData(data, 0, 0);

  return (await kanvas.convertToBlob({ type: "image/png" })).arrayBuffer();
}

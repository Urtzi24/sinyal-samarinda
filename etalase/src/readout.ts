/**
 * Angka yang muncul saat satu titik ditekan, bentuk ringkas.
 *
 * Menampilkan tingkat DAN nilai teknis berdampingan: tingkat melayani orang
 * yang mau pindah kos, nilai teknis melayani orang yang ingin memeriksa hasil
 * hitungannya. Keduanya bertanda prediksi.
 *
 * Peringatan bahwa angkanya ditaksir terlalu kuat tetap menempel di sini —
 * FR-025 mewajibkannya terbaca di dekat tempat angka itu muncul, bukan cuma di
 * daftar batasan.
 */

import { OPERATOR_NAMES, type OperatorId } from "./map";
import { SIGNAL_LABELS, SIGNAL_STEPS, signalLevel } from "./palette";

export type Sample = { dbm: number; adequate: boolean; insideCity: boolean } | null;

export function renderReadout(
  target: HTMLElement,
  operator: OperatorId,
  contoh: Sample,
): void {
  if (!contoh) {
    target.hidden = true;
    return;
  }
  target.hidden = false;

  if (!contoh.insideCity) {
    target.innerHTML = `<p class="titik__kosong">Di luar batas Kota Samarinda</p>`;
    return;
  }

  if (!contoh.adequate) {
    target.innerHTML = `
      <p class="titik__operator">${OPERATOR_NAMES[operator]}</p>
      <p class="titik__nodata">Data tidak memadai</p>
      <p class="titik__catatan">
        Tidak ada menara operator ini yang terdaftar cukup dekat. Bukan berarti
        sinyalnya jelek &mdash; berarti datanya tidak ada.
      </p>`;
    return;
  }

  const tingkat = signalLevel(contoh.dbm);
  target.innerHTML = `
    <p class="titik__operator">${OPERATOR_NAMES[operator]}</p>
    <p class="titik__tingkat">
      <span class="titik__kotak" style="background:${SIGNAL_STEPS[tingkat]}"></span>
      <span class="numeric">${tingkat + 1}</span>/<span class="numeric">${SIGNAL_STEPS.length}</span>
      &mdash; ${SIGNAL_LABELS[tingkat]}
    </p>
    <p class="titik__dbm">
      <output class="numeric">${contoh.dbm.toFixed(0)} dBm</output>
      <span class="titik__tanda">prediksi</span>
    </p>
    <p class="titik__catatan">
      Angka ini <strong>ditaksir terlalu kuat</strong>. Yang bisa dipercaya
      perbandingannya &mdash; antar operator, dan antar daerah.
    </p>`;
}

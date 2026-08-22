/**
 * Keterangan warna, bentuk ringkas.
 *
 * Tetap WAJIB selalu terlihat selama peta ditampilkan — tanpa ini warna di peta
 * tidak berarti apa-apa. Yang berubah cuma bentuknya: dari daftar bertumpuk
 * dengan dua paragraf penjelasan, jadi satu baris mendatar di kaki layar.
 */

import { NO_DATA_COLOR, SIGNAL_LABELS, SIGNAL_STEPS } from "./palette";

export function renderLegend(target: HTMLElement): void {
  const kotak = SIGNAL_STEPS.map(
    (warna, i) =>
      `<span class="warna__kotak" style="background:${warna}" title="${SIGNAL_LABELS[i]}"></span>`,
  ).join("");

  target.innerHTML = `
    <span class="warna__ujung">lemah</span>
    <span class="warna__deret">${kotak}</span>
    <span class="warna__ujung">kuat</span>
    <span class="warna__pisah"></span>
    <span class="warna__kotak warna__kotak--arsir" style="--no-data:${NO_DATA_COLOR}"></span>
    <span class="warna__ujung">tidak terdata</span>`;
}

/**
 * Tabel perkiraan per kecamatan — cara membaca peta ini tanpa melihat peta.
 *
 * FR-013. Bukan ringkasan dan bukan pelengkap: angkanya persis angka yang
 * mewarnai peta, dihitung dari kisi yang sama, cuma dikelompokkan per kecamatan.
 *
 * Yang membuatnya perlu ada: gradasi warna tidak menyampaikan apa pun ke
 * pembaca layar, dan menyampaikan lebih sedikit dari yang dikira ke mata yang
 * membedakan warna secara berbeda. Tabel ini bukan versi "aksesibel" yang
 * dikurangi — untuk sebagian orang ia satu-satunya versi yang ada.
 *
 * Warna di tiap sel cuma penguat. Yang membawa artinya teks: nama tingkat,
 * angka dBm, dan rentangnya. Kalau seluruh warna dicabut, tabelnya tetap utuh.
 */

import { OPERATOR_NAMES, OPERATORS, type OperatorId } from "./map";
import { SIGNAL_LABELS, SIGNAL_STEPS, signalLevel } from "./palette";

type Perkiraan = {
  dbm_tengah: number | null;
  dbm_bawah: number | null;
  dbm_atas: number | null;
  sel: number;
  sel_memadai: number;
};

type Kecamatan = {
  nama: string;
  operator: Record<OperatorId, Perkiraan>;
};

export type Ringkasan = {
  kerincian_m: number;
  kecamatan: Kecamatan[];
};

/**
 * Di bawah bagian ini, bolongnya data cukup besar untuk perlu disebut.
 *
 * Sembilan puluh persen dipilih karena di situlah selisih antar operator mulai
 * jadi selisih kelengkapan data, bukan selisih sinyal. XLSmart di Palaran cuma
 * punya data untuk 51% wilayahnya; tanpa peringatan, angkanya terbaca seolah
 * mewakili seluruh kecamatan.
 */
const AMBANG_KELENGKAPAN = 0.9;

function selPerkiraan(nilai: Perkiraan): string {
  if (nilai.dbm_tengah === null) {
    return `<td class="tabel__sel tabel__sel--kosong">Tidak terdata</td>`;
  }

  const tingkat = signalLevel(nilai.dbm_tengah);
  const lengkap = nilai.sel_memadai / nilai.sel;
  const catatan =
    lengkap < AMBANG_KELENGKAPAN
      ? `<span class="tabel__bolong">dari ${Math.round(lengkap * 100)}% wilayah yang terdata</span>`
      : "";

  return `
    <td class="tabel__sel">
      <span class="tabel__tingkat">
        <span class="tabel__kotak" style="background:${SIGNAL_STEPS[tingkat]}" aria-hidden="true"></span>
        ${SIGNAL_LABELS[tingkat]}
      </span>
      <span class="tabel__angka numeric">${nilai.dbm_tengah.toFixed(0)} dBm</span>
      <span class="tabel__rentang numeric">${nilai.dbm_atas!.toFixed(0)} sampai ${nilai.dbm_bawah!.toFixed(0)}</span>
      ${catatan}
    </td>`;
}

export function renderTable(target: HTMLElement, ringkasan: Ringkasan): void {
  const kepala = OPERATORS.map(
    (id) => `<th scope="col">${OPERATOR_NAMES[id]}</th>`,
  ).join("");

  const baris = ringkasan.kecamatan
    .map(
      (k) => `
      <tr>
        <th scope="row" class="tabel__nama">${k.nama}</th>
        ${OPERATORS.map((id) => selPerkiraan(k.operator[id])).join("")}
      </tr>`,
    )
    .join("");

  target.innerHTML = `
    <table class="tabel__isi">
      <caption class="tabel__keterangan">
        Perkiraan kekuatan sinyal tiap operator di sepuluh kecamatan Kota
        Samarinda, dihitung pada kisi ${ringkasan.kerincian_m} meter. Tiap sel
        menyebut tingkatnya, angka tengahnya, lalu rentang dari bagian terbaik
        sampai terburuk kecamatan itu. Angka dBm ditaksir terlalu kuat
        &mdash; yang bisa dipercaya perbandingannya.
      </caption>
      <thead>
        <tr>
          <th scope="col">Kecamatan</th>
          ${kepala}
        </tr>
      </thead>
      <tbody>${baris}</tbody>
    </table>`;
}

/** Ambil ringkasan yang sudah dihitung dapur. */
export async function loadSummary(): Promise<Ringkasan> {
  const jawaban = await fetch("/ubin/ringkasan-kecamatan.json");
  if (!jawaban.ok) throw new Error(`ringkasan kecamatan: HTTP ${jawaban.status}`);
  return (await jawaban.json()) as Ringkasan;
}

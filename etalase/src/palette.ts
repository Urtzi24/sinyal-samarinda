/**
 * Skema warna kekuatan sinyal.
 *
 * Ini keputusan teknis, bukan selera, dan aturannya terkunci di PRD bagian 10.
 * Semua nilai di bawah sudah lolos pemeriksaan skala berurutan: satu warna
 * dasar, terang menurun berurutan, tiap langkah cukup jauh untuk terbaca, dan
 * ujung paling terang masih memisah dari latar.
 *
 * Kenapa satu warna dasar saja: skema merah-hijau dilarang karena sekitar 8%
 * laki-laki tidak bisa membedakannya, dan merekalah pembaca utama peta ini.
 * Satu warna dengan terang berurutan menyelesaikan itu sekaligus membuat
 * urutannya tetap terbaca kalau dicetak hitam-putih.
 */

/** Latar peta: krem keabuan. */
export const SURFACE = "#e8e4dc";

/** Warna tinta untuk teks di atas latar itu. */
export const INK = "#2b2924";
export const INK_MUTED = "#6b665c";

/**
 * Enam tingkat, dari sinyal terlemah ke terkuat.
 *
 * Dibagi bertingkat, bukan gradasi mulus: orang tidak bisa membaca gradasi
 * mulus jadi angka, dan tingkatan lebih jujur terhadap ketelitian prediksi yang
 * memang tidak setinggi itu.
 */
export const SIGNAL_STEPS = [
  "#63aca7",
  "#47948f",
  "#2e7d79",
  "#1a6663",
  "#0f504e",
  "#073b39",
] as const;

/**
 * Ambang batas tiap tingkat dalam dBm.
 *
 * Angka-angka ini TIDAK diambil dari tabel mutu sinyal mana pun. Mereka diambil
 * dari sebaran hasil hitung Samarinda sendiri — persentil 17, 33, 50, 67, dan 83
 * dari 52.748 sel yang datanya memadai, ketiga operator digabung. Jadi tiap
 * tingkat memikul kira-kira seperenam wilayah kota.
 *
 * Kenapa begitu dan bukan memakai ambang baku: perhitungan Tahap A menaksir daya
 * terima terlalu kuat sekitar 30-50 dB, karena belum memasukkan arah antena dan
 * redaman gedung. Memakai ambang mutlak berarti hampir seluruh kota masuk
 * tingkat teratas, dan peta yang rata gelap tidak membedakan apa pun.
 *
 * Konsekuensinya jujur: tingkat di peta ini menyatakan posisi RELATIF terhadap
 * Samarinda, bukan mutu mutlak. Angka ini wajib dihitung ulang kalau modelnya
 * berubah — misalnya saat naik ke ITU-R P.1812.
 */
export const SIGNAL_BREAKS_DBM = [-75, -62, -50, -40, -30] as const;

/** Nama tiap tingkat, untuk keterangan warna dan untuk pembaca layar. */
export const SIGNAL_LABELS = [
  "sangat lemah",
  "lemah",
  "sedang",
  "cukup",
  "kuat",
  "sangat kuat",
] as const;

/**
 * Warna wilayah yang tidak punya cukup data.
 *
 * Terhadap tingkat sinyal terlemah kontrasnya cuma 1,76:1 — terlalu dekat untuk
 * dibedakan dari warnanya saja. Karena itu wilayah ini WAJIB diberi arsir. Arsir
 * yang jadi pembeda utamanya; warnanya cuma penguat.
 *
 * Bedanya penting: 36% wilayah Samarinda tidak punya data XLSmart. Tanpa
 * pembedaan ini, operator itu akan terlihat buruk di seluruh kota padahal yang
 * terjadi menaranya tidak terdaftar.
 */
export const NO_DATA_COLOR = "#7a746a";

/** Tingkat keberapa sebuah nilai dBm jatuh, 0 sampai 5. */
export function signalLevel(dbm: number): number {
  let level = 0;
  for (const batas of SIGNAL_BREAKS_DBM) {
    if (dbm >= batas) level += 1;
  }
  return level;
}

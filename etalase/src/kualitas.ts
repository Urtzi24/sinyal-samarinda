/**
 * Penurunan kerincian otomatis pada perangkat yang tidak sanggup — FR-018.
 *
 * Yang mahal di peta ini tiga: bentang alam 3D (mengurai ubin ketinggian lalu
 * membentuk jala di GPU), gedung ber-ekstrusi (puluhan ribu poligon didorong
 * naik tiap gambar), dan bayangan bukit (menghitung lereng tiap piksel).
 * Ketiganya hiasan. Warna sinyalnya — satu-satunya alasan peta ini ada — murah,
 * karena cuma raster yang ditempel.
 *
 * Jadi kalau perangkatnya tidak sanggup, yang dilepas hiasannya, dan petanya
 * tetap menjawab pertanyaannya. Itu maksud FR-018: turun kerincian, bukan gagal
 * terbuka.
 *
 * Dua lapis pemeriksaan, karena satu saja tidak cukup:
 *
 * 1. **Sebelum menggambar**, dari keterangan perangkat. Ini yang menyelamatkan
 *    perangkat yang paling lemah — mereka tidak sempat mencoba lalu gagal,
 *    melainkan tidak pernah mencoba.
 * 2. **Sesudah berjalan**, dari waktu gambar sebenarnya. Keterangan perangkat
 *    bohong dan tidak ada di semua peramban; yang tidak bisa bohong adalah
 *    berapa lama satu gambar sebenarnya makan waktu.
 *
 * Sekali turun, tidak pernah naik lagi sendiri. Peta yang tersendat lalu mulus
 * lalu tersendat lagi lebih menyiksa daripada peta yang tenang di kerincian
 * rendah.
 */

export type Tingkat = "penuh" | "ringan";

/**
 * Ingatan perangkat, dalam gigabita, yang di bawahnya hiasan langsung dilepas.
 *
 * `navigator.deviceMemory` dilaporkan dibulatkan ke pangkat dua, dan 2 GB
 * adalah kelas ponsel Android yang paling banyak beredar di Indonesia. Di kelas
 * itu, menyalakan bentang alam 3D bukan membuat peta lambat melainkan membuat
 * tabnya ditutup paksa.
 */
const INGATAN_MINIMUM_GB = 2;

/** Jumlah inti prosesor yang di bawahnya dianggap tidak sanggup. */
const INTI_MINIMUM = 4;

/**
 * Waktu satu gambar yang di atasnya peta dianggap tersendat, milidetik.
 *
 * Lima puluh milidetik kira-kira 20 gambar per detik. Di bawah itu, menggeser
 * peta terasa patah-patah, bukan sekadar kurang mulus. Ambangnya sengaja jauh
 * dari 16,7 ms (60 gambar per detik): yang dicari perangkat yang kepayahan,
 * bukan perangkat yang sesekali tersendat.
 */
const AMBANG_TERSENDAT_MS = 50;

/**
 * Berapa gambar berturut-turut yang harus lambat sebelum kerincian diturunkan.
 *
 * Beberapa gambar pertama SELALU lambat — ubin sedang diurai, huruf sedang
 * dipasang, jala bentang alam sedang dibentuk. Menurunkan kerincian karena itu
 * berarti tidak ada perangkat yang pernah dapat kerincian penuh.
 */
const GAMBAR_LAMBAT_BERTURUT = 20;

/** Gambar-gambar pertama yang diabaikan, karena pasti lambat. */
const GAMBAR_PEMANASAN = 40;

type NavigatorDenganIngatan = Navigator & { deviceMemory?: number };

/**
 * Tingkat yang dipilih sebelum satu gambar pun dibuat.
 *
 * Keterangan yang tidak ada dianggap sanggup, bukan tidak sanggup. Safari dan
 * Firefox tidak melaporkan `deviceMemory` sama sekali; menganggap diamnya
 * sebagai perangkat lemah akan mencabut bentang alam 3D dari semua penggunanya.
 */
export function tingkatAwal(nav: Navigator = navigator): Tingkat {
  const ingatan = (nav as NavigatorDenganIngatan).deviceMemory;
  if (typeof ingatan === "number" && ingatan < INGATAN_MINIMUM_GB) return "ringan";

  const inti = nav.hardwareConcurrency;
  if (typeof inti === "number" && inti > 0 && inti < INTI_MINIMUM) return "ringan";

  return "penuh";
}

/**
 * Awasi waktu gambar; panggil `turunkan` sekali kalau peta ternyata tersendat.
 *
 * Mengembalikan fungsi penghenti, supaya pengawasannya bisa dilepas.
 */
export function awasiKinerja(turunkan: () => void): () => void {
  let gambar = 0;
  let lambatBerturut = 0;
  let sebelumnya = performance.now();
  let hidup = true;

  const langkah = (sekarang: number) => {
    if (!hidup) return;
    const selang = sekarang - sebelumnya;
    sebelumnya = sekarang;
    gambar += 1;

    if (gambar > GAMBAR_PEMANASAN) {
      lambatBerturut = selang > AMBANG_TERSENDAT_MS ? lambatBerturut + 1 : 0;
      if (lambatBerturut >= GAMBAR_LAMBAT_BERTURUT) {
        hidup = false;
        turunkan();
        return;
      }
    }
    requestAnimationFrame(langkah);
  };

  requestAnimationFrame(langkah);
  return () => {
    hidup = false;
  };
}

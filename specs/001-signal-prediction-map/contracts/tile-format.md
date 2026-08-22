# Kontrak: format ubin sinyal

**Antara:** `dapur/tiles/` (Python, menulis) ↔ `etalase/src/map.ts` (TypeScript, membaca)

Ini kontrak yang paling gampang rusak diam-diam. Kalau kedua sisi tidak sepakat
persis, petanya tetap tampil — cuma angkanya salah, dan tidak ada yang tahu.
Karena itu penyandian dan pembacaannya wajib punya tes pulang-pergi di kedua sisi.

---

## Bentuk berkas

- PNG, 256 × 256 piksel, RGBA 8 bit per kanal.
- Skema alamat ubin Web Mercator (`z/x/y`), sama seperti ubin peta pada umumnya.
- Satu arsip PMTiles per operator: `sinyal-{operator_id}.pmtiles`.
- Arsip ketinggian terpisah dan dipakai bersama semua operator:
  `ketinggian.pmtiles`.

## Arti tiap kanal

| Kanal | Isi | Jangkauan |
|---|---|---|
| **R** | 8 bit atas nilai sinyal | 0–255 |
| **G** | 8 bit bawah nilai sinyal | 0–255 |
| **B** | kecukupan data | 0 = tidak memadai, 255 = memadai |
| **A** | di dalam batas kota | 0 = luar, 255 = dalam |

## Rumus penyandian

Menulis (dapur):

```
nilai  = clamp(round((daya_dbm + 140) * 10), 0, 1800)
R      = nilai >> 8
G      = nilai & 255
```

Membaca (etalase):

```
nilai    = (R << 8) | G
daya_dbm = nilai / 10 - 140
```

**Jangkauan yang tercakup:** −140 dBm sampai +40 dBm, langkah 0,1 dB.

Batas atas 1800 dipilih supaya nilai selalu muat di 16 bit dengan sisa. Nilai di
luar jangkauan **dipangkas, bukan dilipat** — melipat menghasilkan angka yang
tampak wajar padahal salah.

## Aturan yang mengikat

1. **Kanal biru dibaca lebih dulu.** Kalau `B = 0`, nilai R–G **dilarang
   ditampilkan sebagai angka sinyal**. Yang muncul harus keterangan "data tidak
   memadai". Ini FR-011, dan Langkah 0 membuktikan ini sering terjadi — XLSmart
   cuma memegang 5% data.
2. **Kanal alfa dibaca sebelum keduanya.** `A = 0` berarti titik itu di luar Kota
   Samarinda; peta menyatakan di luar cakupan, bukan memberi angka.
3. **Nilai disimpan sebagai daya terima, bukan warna.** Skema warna hidup
   sepenuhnya di etalase. Mengganti skema warna tidak boleh menyentuh dapur —
   inilah alasan penyandian ini dipilih, dan itu keputusan terkunci di PRD
   bagian 14.
4. **Langkah 0,1 dB adalah ketelitian penyimpanan, bukan ketelitian model.**
   Yang ditampilkan ke pengguna wajib dibulatkan. Peta dilarang memamerkan
   ketelitian yang tidak dimilikinya.

## Tes yang wajib ada

| Tes | Di mana | Yang dibuktikan |
|---|---|---|
| Pulang-pergi penyandian | `tests/tiles/` | `baca(tulis(x)) == x` untuk seluruh jangkauan −140…+40 dBm |
| Pemangkasan | `tests/tiles/` | Nilai di luar jangkauan dipangkas, tidak melipat |
| Kesepakatan dua sisi | `tests/tiles/` + Vitest | Ubin contoh yang ditulis Python dibaca TypeScript dan menghasilkan angka yang sama |

Tes ketiga yang paling penting. Dua tes pertama bisa lolos di kedua sisi sambil
tetap salah, kalau salahnya sama-sama konsisten di sisi masing-masing.

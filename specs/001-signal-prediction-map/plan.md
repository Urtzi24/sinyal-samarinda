# Rencana Implementasi: Peta Prediksi Sinyal Samarinda (Tahap 1)

**Branch**: `001-signal-prediction-map` (folder spesifikasi; repo masih di `master`, tanpa cabang khusus) | **Tanggal**: 2026-08-14 | **Spesifikasi**: [spec.md](spec.md)

**Masukan**: Spesifikasi fitur dari `specs/001-signal-prediction-map/spec.md`

## Summary

Menghitung perkiraan kekuatan sinyal untuk seluruh Kota Samarinda, per operator,
dari posisi pemancar dan bentuk permukaan tanah — lalu menyajikannya sebagai peta
3D yang bisa dibuka siapa saja tanpa server yang menghitung apa pun.

Pendekatan teknisnya: **dapur Python menghitung lebih dulu di laptop**, hasilnya
disandikan ke ubin PNG dan dibungkus PMTiles, lalu **etalase TypeScript** membaca
potongan ubin itu langsung lewat HTTP. Perhitungan propagasinya dibangun sendiri
dan diuji terhadap angka acuan resmi ITU — itu bagian yang tidak bisa disalin, dan
itu inti nilai proyeknya.

## Technical Context

**Language/Version**: Python 3.12 (dapur) · TypeScript (etalase)

**Primary Dependencies**: NumPy, rasterio, pyproj, Pillow, pmtiles (dapur) ·
Vite, MapLibre GL JS (etalase). Pillow dan pmtiles adalah tambahan di luar daftar
PRD bagian 9 — alasannya di [research.md](research.md).

**Storage**: Berkas di cakram. Tidak ada basis data di Tahap 1. Keluaran akhir
berupa arsip PMTiles statis.

**Testing**: pytest (dapur) · Vitest (etalase)

**Target Platform**: Peramban web, wajib jalan di ponsel kelas menengah. Dapur
jalan di laptop Windows.

**Project Type**: Pipa perhitungan luring + halaman web statis

**Performance Goals**: Peta bisa diputar/dimiringkan tanpa tersendat di ponsel
kelas menengah. Satu putaran penuh dapur pada kerincian kasar selesai dalam
hitungan menit, bukan jam — supaya iterasinya tidak menyiksa.

**Constraints**: Nol perhitungan sisi server saat halaman dibuka. Nol kunci API
berbayar. Seluruh keluaran harus muat di paket hosting gratis dan disajikan lewat
HTTP range request.

**Scale/Scope**: Kota Samarinda, 27 × 45 km. Tiga operator. Perkiraan keluaran
~4.700 ubin per operator untuk zoom 10–16, total ubin sinyal + ketinggian di
kisaran **200–350 MB** — jauh di bawah batas gratis Cloudflare R2 (10 GB).
Perhitungannya sendiri ~1,35 juta sel per operator pada kerincian 30 m.

## Constitution Check

*GERBANG: harus lolos sebelum riset Phase 0. Diperiksa ulang setelah desain Phase 1.*

| Prinsip | Putusan | Bagaimana rencana ini memenuhinya |
|---|---|---|
| I. Rumus fisika berbukti angka acuan | **Lolos** | Model yang dipilih (ITU-R P.526 lalu P.1812) menerbitkan data validasi resmi. Tes acuan ditulis lebih dulu; ubin tidak boleh dihasilkan dari rumus yang belum punya tes |
| II. Nol angka ajaib | **Lolos** (syarat dipenuhi 14 Agustus 2026, T007) | Parameter pemancar tidak ada di data dan harus diasumsikan. Seluruhnya kini bernama dan bersumber ke Report ITU-R M.2292-0 Tabel 2 dan 3 kolom Macro urban, serta 3GPP TR 38.901 untuk tinggi penerima |
| III. Matematika sebagai fungsi murni | **Lolos** | `dapur/propagation/` murni NumPy, tanpa I/O. Unduhan dan penulisan ubin dipisah ke `dapur/io/` |
| IV. Dapur bisa dilanjutkan | **Lolos** | Perhitungan dipecah per ubin; ubin yang sudah jadi dilewati saat dijalankan ulang |
| V. Data mentah di luar git | **Lolos** | `data/` sudah di `.gitignore`. Yang masuk git skrip pengunduh + `LANGKAH-0.md` |
| VI. Ketidakpastian ditampilkan | **Lolos** | FR-012. Rencana ini **menambah satu batasan baru**: parameter pemancar diasumsikan, bukan diketahui |
| VII. Nol kunci API berbayar | **Lolos dengan syarat** | Copernicus DEM tanpa kunci sama sekali. OpenCelliD perlu token **gratis** — bukan berbayar, jadi tidak melanggar. Tapi token itu **wajib lewat variabel lingkungan** dan dilarang masuk git |
| VIII. Commit bersih berbahasa Indonesia | **Lolos** | Proses, bukan kode |

**Batasan mengikat lain:** tumpukan teknologi mengikuti PRD bagian 9 tanpa
perubahan. Dua pustaka ditambahkan dengan alasan tertulis. Susunan folder
mengikuti PRD bagian 11 persis.

### Pemeriksaan ulang setelah desain Phase 1

Desain memperkuat empat prinsip dan **membuka satu lubang baru**:

| Prinsip | Perubahan setelah desain |
|---|---|
| I | **Menguat.** [`quickstart.md`](quickstart.md) langkah 1 menjadikan tes acuan sebagai gerbang: gagal di situ, berhenti — dilarang menghasilkan ubin |
| II | **Tetap bersyarat.** [`research.md`](research.md) bagian 3 mendaftar tiap asumsi pemancar. Syaratnya mengikat: tanpa rujukan di komentar, konstanta itu belum boleh dipakai menghasilkan ubin |
| III | **Menguat.** [`contracts/dapur-cli.md`](contracts/dapur-cli.md) aturan 3 melarang `hitung` menyentuh jaringan sama sekali |
| IV | **Menguat.** Punya cara ujinya sendiri — quickstart langkah 4 menghentikan dapur di tengah lalu memastikan jalan kedua melanjutkan |
| VI | **Lubang ditemukan, lalu ditutup** — lihat di bawah |
| VII | **Menguat.** Token lewat variabel lingkungan, gagal dengan pesan jelas kalau kosong |

**Lubang di Prinsip VI.** Riset Phase 0 menemukan bahwa frekuensi, tinggi antena,
dan daya pancar **tidak ada di data mana pun** dan harus diasumsikan. Asumsi itu
kemungkinan menyumbang kesalahan lebih besar daripada model propagasinya sendiri —
menganggap semua pemancar sama tinggi dan sama kuat berarti perbedaan antar lokasi
datang hampir seluruhnya dari jarak dan medan.

Prinsip VI mewajibkan ketidakpastian ditampilkan di peta. Batasan ini semula tidak
ada di PRD bagian 7 maupun di spesifikasi, sehingga rancangan ini sempat **tidak**
memenuhi Prinsip VI.

**Sudah ditutup pada 14 Agustus 2026, disetujui Ali:**

- **PRD bagian 7 poin 5 (baru)** — menyatakan parameter pemancar diasumsikan, dan
  menyebutnya kemungkinan sumber kesalahan terbesar di seluruh peta.
- **FR-024 (baru)** — mewajibkan pernyataan itu terbaca di halaman, bersama
  batasan lain di FR-012.
- **Asumsi baru di spesifikasi** — mencatat konsekuensinya: karena semua pemancar
  dianggap sama, perbedaan antar lokasi datang hampir seluruhnya dari jarak dan
  bentuk tanah.

**Putusan akhir: kedelapan prinsip lolos.**

Syarat Prinsip II sudah dipenuhi pada 14 Agustus 2026 (T007): seluruh asumsi
pemancar kini bersumber ke Report ITU-R M.2292-0 Tabel 2 dan 3 kolom *Macro
urban*, dan tinggi penerima ke 3GPP TR 38.901. Tidak ada lagi angka tanpa
asal-usul di `dapur/constants.py`.

## Project Structure

### Documentation (this feature)

```text
specs/001-signal-prediction-map/
├── plan.md              # Berkas ini
├── research.md          # Keluaran Phase 0
├── data-model.md        # Keluaran Phase 1
├── quickstart.md        # Keluaran Phase 1
├── contracts/           # Keluaran Phase 1
└── tasks.md             # Rincian tugas — belum dibuat
```

### Source Code (repository root)

```text
dapur/
├── sources/             # unduh: OpenCelliD, Copernicus DEM. Menyentuh jaringan
├── propagation/         # fungsi murni: path loss, difraksi, profil medan
├── grid/                # bangun kisi hitung, ubah koordinat
├── tiles/               # sandikan nilai ke RGB, tulis PNG, bungkus PMTiles
├── constants.py         # semua asumsi bernama, tiap satu ada sumbernya
└── run.py               # perangkai; satu-satunya yang tahu urutan langkah

etalase/
├── src/
│   ├── map.ts           # penyiapan MapLibre, lapisan medan + sinyal
│   ├── operators.ts     # tombol pemilih operator
│   ├── legend.ts        # keterangan warna
│   ├── readout.ts       # angka saat titik ditekan (FR-022)
│   └── table.ts         # jalur baca tanpa peta, per kecamatan (FR-013)
└── index.html

kotak-surat/             # Tahap 2 saja — kosong
data/                    # data mentah & hasil hitung — tidak masuk git
docs/                    # PRD, konstitusi rujukan, LANGKAH-0
tests/
├── propagation/         # tes angka acuan — Prinsip I
├── tiles/               # tes sandi RGB pulang-pergi
└── grid/
```

**Structure Decision**: Mengikuti susunan folder yang sudah dikunci di PRD bagian
11 — `dapur/`, `etalase/`, `kotak-surat/`, `data/`, `docs/`. Pemisahan
`propagation/` dari `sources/` dan `tiles/` bukan selera: Prinsip III mewajibkan
matematikanya bebas I/O supaya bisa diuji, dan itu cuma bisa dijamin kalau
pemisahannya ada di tingkat folder.

## Complexity Tracking

| Pelanggaran | Kenapa perlu | Alternatif sederhana ditolak karena |
|---|---|---|
| Parameter pemancar diasumsikan, menegangkan Prinsip II | Data terbuka tidak memuat tinggi antena, daya pancar, maupun frekuensi. Tanpa asumsi, tidak ada perhitungan yang bisa dijalankan sama sekali | Menunggu data sebenarnya berarti proyek tidak pernah mulai — operator tidak menerbitkannya. Menghapus parameter dari rumus berarti membuang fisikanya |
| Dua pustaka di luar daftar PRD bagian 9 (`Pillow`, `pmtiles`) | Menulis berkas PNG dan arsip PMTiles dari nol adalah pekerjaan yang sudah dipecahkan orang lain, dan bukan bagian yang membuat proyek ini bernilai | Menulis penyandi PNG sendiri menghabiskan waktu di tempat yang salah — PRD bagian 8 sudah menetapkan prinsip ini untuk MapLibre |

---
description: "Daftar tugas Tahap 1 — Peta Prediksi Sinyal Samarinda"
---

# Tugas: Peta Prediksi Sinyal Samarinda (Tahap 1)

**Masukan**: dokumen rancangan di `specs/001-signal-prediction-map/`

**Prasyarat**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/)

**Tes**: **diminta, dan wajib.** Konstitusi Prinsip I melarang rumus fisika dipakai
menghasilkan ubin sebelum punya tes berangka acuan. Tes ditulis lebih dulu dan
harus gagal sebelum rumusnya ada.

**Lingkup**: Tahap 1 saja. `kotak-surat/` tetap kosong.

## Format: `[ID] [P?] [Story] Deskripsi`

- **[P]**: bisa dikerjakan bersamaan (berkas berbeda, tidak saling menunggu)
- **[Story]**: cerita pengguna yang dilayani (US1, US2, US3)
- Tiap tugas menyebut jalur berkasnya

---

## Phase 1: Persiapan

**Tujuan**: kerangka proyek berdiri.

- [x] T001 Buat susunan folder sesuai plan.md: `dapur/`, `etalase/`, `kotak-surat/`, `data/`, `tests/` di akar repo
- [x] T002 Inisialisasi proyek Python dengan `uv` di `pyproject.toml`, tambahkan NumPy, rasterio, pyproj, Pillow, pmtiles, pytest, ruff
- [x] T003 [P] Konfigurasi ruff sebagai pemeriksa gaya sekaligus pemformat di `pyproject.toml`
- [x] T004 [P] Inisialisasi etalase dengan Vite + TypeScript + Vitest di `etalase/package.json`
- [x] T005 [P] Tambahkan MapLibre GL JS dan berkas huruf yang disimpan sendiri di `etalase/` — IBM Plex Sans + IBM Plex Mono, dipilih Ali 14 Agustus 2026

---

## Phase 2: Fondasi (prasyarat yang memblokir)

**Tujuan**: dapur menghasilkan ubin. Tanpa ini tidak ada cerita pengguna yang bisa jalan — peta tanpa data bukan peta.

**⚠️ KRITIS**: tidak ada pekerjaan etalase yang boleh dimulai sebelum fase ini selesai.

### Konstanta — Prinsip II

- [x] T006 Tulis konstanta sumber data, kotak batas Samarinda, dan pemetaan MNC→operator di `dapur/constants.py`, tiap satu dengan sumbernya di komentar
- [x] T007 Tulis konstanta asumsi pemancar (frekuensi per jenis radio, tinggi antena, EIRP, tinggi penerima) di `dapur/constants.py` — rujukan: Report ITU-R M.2292-0 Tabel 2 & 3 kolom *Macro urban*, dan 3GPP TR 38.901 untuk tinggi penerima

### Tes angka acuan — ditulis lebih dulu, harus GAGAL

- [x] T008 [P] Tulis tes angka acuan redaman ruang bebas di `tests/propagation/test_free_space.py` — sumber ITU-R P.525-5 pers. (5) dan (6)
- [x] T009 [P] Tulis tes angka acuan difraksi ITU-R P.526 di `tests/propagation/test_diffraction.py`, memakai contoh perhitungan dari teks rekomendasinya — pers. (26), (31), (33)

### Rumus propagasi — fungsi murni, Prinsip III

- [x] T010 Implementasi redaman ruang bebas di `dapur/propagation/free_space.py` — tanpa I/O, tanpa jam sistem
- [x] T011 Implementasi difraksi mata pisau tunggal ITU-R P.526 di `dapur/propagation/diffraction.py`
- [x] T012 Implementasi penggabungan Deygout untuk banyak penghalang di `dapur/propagation/diffraction.py`
- [x] T013 **GERBANG LOLOS** (14 Agustus 2026): 27 tes acuan propagasi lolos. Tes medan datar menangkap satu kesalahan nyata — penghalang harus berupa puncak, bukan sembarang titik cuplik

### Sumber data

- [x] T014 [P] Pengunduh ubin Copernicus DEM di `dapur/sources/dem.py`
- [x] T015 [P] Pengunduh OpenCelliD di `dapur/sources/opencellid.py` — token dari `OPENCELLID_TOKEN`, berhenti dengan pesan jelas kalau kosong, dilarang ada token contoh di kode
- [x] T016 Penyaring ke Samarinda + pemeta MNC→operator + pembuang baris tidak sah di `dapur/sources/transmitters.py`, sesuai aturan sah di data-model.md

### Kisi dan medan

- [x] T017 [P] Pembangun kisi hitung dan pengubah koordinat di `dapur/grid/build.py`
- [x] T018 Pengambil profil medan dari DEM di `dapur/grid/profile.py` — pencuplikan serapat 30 m, dibatasi 128 titik per profil untuk lintasan panjang
- [x] T019 Perangkai daya terima per sel (ambil pemancar terkuat, bukan dijumlahkan) di `dapur/propagation/received_power.py` — terukur ~25 detik per operator di kisi kasar

### Ubin

- [x] T020 [P] Tulis tes pulang-pergi sandi RGB di `tests/test_tiles.py` — termasuk uji pemangkasan nilai di luar jangkauan
- [x] T021 Implementasi sandi RGB sesuai `contracts/tile-format.md` di `dapur/tiles/encode.py`
- [x] T022 Penulis berkas PNG per ubin di `dapur/tiles/archive.py`
- [x] T023 Pembungkus arsip PMTiles di `dapur/tiles/archive.py` — tidak dinamai `pmtiles.py` supaya tidak tertukar dengan pustakanya
- [x] T024 [P] Pembuat ubin ketinggian dari DEM di `dapur/tiles/terrain.py` — penyandian Terrarium

### Perintah dapur

- [x] T025 Perintah `unduh`, `siapkan`, `hitung`, `ubin`, `semua` sesuai `contracts/dapur-cli.md` di `dapur/run.py`
- [x] T026 Kemampuan melanjutkan: lewati satuan kerja yang keluarannya sudah ada di cakram, di `dapur/run.py` — Prinsip IV
- [x] T027 Tulis tes kemampuan melanjutkan di `tests/test_resume.py`: hentikan di tengah, jalankan lagi, pastikan melanjutkan bukan mengulang
- [x] T028 Laporan berangka di layar tiap langkah (baris dibuang per golongan, jumlah sel, ubin per zoom, **ukuran total keluaran**) di `dapur/run.py`
- [x] T029 **GERBANG LOLOS** (14 Agustus 2026): `semua --kerincian 240` selesai 176 detik, empat arsip PMTiles jadi, total 13,7 MB. Menemukan satu bug nyata — jarak mendatar dipakai sebagai ganti jarak miring

**Checkpoint**: dapur menghasilkan ubin. Pekerjaan etalase boleh dimulai.

---

## Phase 3: User Story 1 — Membandingkan operator di satu daerah (P1) 🎯 MVP

**Tujuan**: orang bisa menjawab "operator mana yang bagus di daerah saya" dalam satu layar.

**Uji mandiri**: beri tautan ke orang yang belum pernah melihatnya, sebut satu nama daerah, minta ia menyebut operator terbaik di sana. Berhasil kalau ia sampai ke jawaban tanpa dijelaskan.

### Tes untuk US1

- [x] T030 [P] [US1] Tulis tes pembacaan sandi RGB di sisi TypeScript, terhadap ubin contoh yang ditulis Python, di `etalase/src/tile.test.ts` — ini tes kesepakatan dua sisi yang diwajibkan `contracts/tile-format.md`

### Implementasi US1

- [x] T031 [US1] Muat arsip PMTiles dan pasang lapisan sinyal di `etalase/src/map.ts`
- [x] T032 [P] [US1] Tombol pemilih operator berjajar — tiga operator, semuanya terlihat sekaligus, bukan menu gulung — di `etalase/src/operators.ts`
- [x] T033 [P] [US1] Skema warna 5–7 tingkat, terang berurutan, bukan merah–hijau, sama untuk semua operator, di `etalase/src/legend.ts`
- [x] T034 [US1] Keterangan warna yang selalu terlihat di `etalase/src/legend.ts`
- [x] T035 [US1] Pergantian operator tanpa memuat ulang dan tanpa menggeser posisi peta di `etalase/src/map.ts`
- [x] T036 [US1] Angka saat titik ditekan: tingkat **dan** nilai teknis berdampingan, bertanda prediksi, di `etalase/src/readout.ts` — FR-022
- [x] T037 [US1] Pembedaan "data tidak memadai" dari "sinyal lemah" lewat kanal biru di `etalase/src/map.ts` dan `etalase/src/readout.ts` — FR-011
- [x] T038 [US1] Penanganan titik di luar batas kota lewat kanal alfa di `etalase/src/readout.ts`
- [x] T039 [P] [US1] Label kecamatan dan kelurahan di `etalase/src/map.ts` — FR-010
- [x] T040 [US1] Teks batasan jujur di halaman, termasuk pernyataan parameter pemancar diasumsikan, di `etalase/index.html` — FR-012 dan FR-024

**Checkpoint**: US1 berjalan sendiri. Ini sudah bisa dipamerkan.

---

## Phase 4: User Story 2 — Melihat sebab, bukan cuma hasil (P2)

**Tujuan**: permukaan 3D memperlihatkan bahwa suatu daerah merah karena terhalang bukit tertentu.

**Uji mandiri**: pilih satu daerah yang diketahui terhalang bukit, miringkan peta, pastikan penghalangnya terlihat tanpa penjelasan tambahan.

- [x] T041 [US2] Lapisan bentang alam 3D dari `ketinggian.pmtiles` di `etalase/src/terrain.ts`
- [x] T042 [US2] Warna sinyal menempel mengikuti permukaan tanah — tidak melayang, tidak tembus — di `etalase/src/map.ts`
- [x] T043 [US2] Bentang alam dibuat redup supaya warna sinyal jadi satu-satunya hal pekat di layar, di `etalase/src/terrain.ts`
- [x] T044 [US2] Putar, miringkan, dan zoom tanpa tersendat di `etalase/src/map.ts`
- [x] T045 [US2] Penurunan kerincian otomatis pada perangkat yang tidak sanggup di `etalase/src/terrain.ts` — FR-018

**Checkpoint**: US1 dan US2 dua-duanya berjalan sendiri.

---

## Phase 5: User Story 3 — Membaca data yang sama tanpa peta (P3)

**Tujuan**: perkiraan bisa dibaca tanpa menyentuh peta. **Prioritas di sini berarti urutan pengerjaan, bukan boleh dilewatkan** — konstitusi mewajibkannya sebelum rilis.

**Uji mandiri**: matikan tampilan peta, telusuri halaman hanya dengan papan ketik dan pembaca layar. Perkiraan tiap operator per kecamatan tetap terbaca dan bisa dibandingkan.

- [x] T046 [P] [US3] Peringkas perkiraan per kecamatan di `dapur/tiles/summary.py`, keluaran ke `data/keluaran/ringkasan-kecamatan.json`
- [x] T047 [US3] Tabel per kecamatan berisi perkiraan tiap operator di `etalase/src/table.ts` — FR-013
- [x] T048 [US3] Jangkauan papan ketik penuh dengan penanda fokus yang terlihat di seluruh kendali `etalase/src/` — FR-014
- [x] T049 [US3] Matikan gerak saat perangkat meminta `prefers-reduced-motion` di `etalase/src/map.ts` — FR-016
- [x] T050 [US3] Tanda dan label pembaca layar untuk peta dan tabel di `etalase/index.html`

**Checkpoint**: ketiga cerita pengguna berjalan sendiri-sendiri.

---

## Phase 6: Perapian dan urusan lintas cerita

- [ ] T051 Panel kendali berubah jadi lembar dari bawah pada layar sempit di `etalase/src/` — FR-017
- [ ] T052 Uji beban langsung di ponsel kelas menengah, bukan di peramban laptop yang dikecilkan
- [x] T053 [P] Periksa kontras seluruh teks memenuhi WCAG 2.2 tingkat AA — FR-015
- [x] T054 Ukur ukuran keluaran sebenarnya, bandingkan dengan perkiraan 200–350 MB, perbarui `research.md` bagian 5 dengan angka nyata
- [x] T055 Naikkan kerincian dari 240 m ke 30 m, ukur waktu hitungnya, catat hasilnya
- [ ] T056 Putuskan tempat unggah berdasarkan ukuran sebenarnya, lalu perbarui PRD bagian 9 — bagian ini sengaja dikosongkan sampai angkanya diketahui
- [ ] T057 Jalankan seluruh tujuh langkah di `quickstart.md`
- [ ] T058 Uji SC-001 dengan orang yang belum pernah melihat petanya — ini satu-satunya ukuran yang tidak bisa diperiksa sendiri

---

## Ketergantungan dan urutan

### Antar fase

- **Persiapan (1)**: tidak menunggu apa pun
- **Fondasi (2)**: menunggu Persiapan. **Memblokir semua cerita pengguna**
- **Cerita pengguna (3–5)**: semuanya menunggu Fondasi selesai
- **Perapian (6)**: menunggu cerita yang diinginkan selesai

Fase Fondasi di proyek ini berat, dan itu memang begitu adanya: seluruh dapur adalah prasyarat. Peta tanpa perkiraan bukan peta.

### Dua gerbang yang tidak boleh dilompati

| Gerbang | Isinya | Kalau dilanggar |
|---|---|---|
| **T013** | seluruh tes angka acuan propagasi lolos | Prinsip I pecah. Peta yang salah tetap tampak indah, dan tidak ada yang menyadarinya |
| **T029** | dapur menghasilkan ubin pada kerincian kasar | menaikkan ke 30 m sebelum alurnya terbukti berarti menunggu berjam-jam untuk mengetahui alurnya salah |

### Di dalam tiap cerita

- Tes ditulis dan **harus gagal** sebelum implementasinya ada
- Konstanta sebelum rumus
- Rumus sebelum perangkai
- Dapur sebelum etalase

### Yang bisa dikerjakan bersamaan

- T003, T004, T005 — persiapan di berkas berbeda
- T008 dan T009 — dua tes acuan, berkas berbeda
- T014 dan T015 — dua pengunduh, sumber berbeda
- T032, T033, T039 — bagian etalase yang tidak saling menyentuh
- Setelah Fondasi selesai, US1, US2, dan US3 bisa dikerjakan paralel kalau ada lebih dari satu orang

## Contoh paralel: Fondasi

```bash
# Dua tes acuan bisa ditulis bersamaan:
Tugas: "Tes angka acuan redaman ruang bebas di tests/propagation/test_free_space.py"
Tugas: "Tes angka acuan difraksi P.526 di tests/propagation/test_diffraction.py"

# Dua pengunduh bisa ditulis bersamaan:
Tugas: "Pengunduh Copernicus DEM di dapur/sources/dem.py"
Tugas: "Pengunduh OpenCelliD di dapur/sources/opencellid.py"
```

---

## Cara mengerjakan

### MVP dulu — US1 saja

1. Selesaikan Phase 1
2. Selesaikan Phase 2 — **kritis, memblokir semuanya**
3. Selesaikan Phase 3
4. **BERHENTI dan periksa** US1 berdiri sendiri
5. Sudah bisa dipamerkan

### Bertahap

1. Persiapan + Fondasi → dapur menghasilkan ubin
2. US1 → periksa sendiri → **MVP, sudah layak dipamerkan**
3. US2 → periksa sendiri → sekarang petanya menjelaskan sebab
4. US3 → periksa sendiri → sekarang semua orang bisa memakainya
5. Perapian → naik ke kerincian 30 m, putuskan tempat unggah, uji ke orang sungguhan

PRD bagian 12 menyebut "proyek terlalu besar lalu ditinggalkan" sebagai risiko nyata. Urutan ini jawabannya: berhenti setelah US1 pun sudah ada yang utuh untuk ditunjukkan.

---

## Catatan

- Tugas [P] = berkas berbeda, tidak saling menunggu
- Tes wajib gagal dulu sebelum implementasinya ditulis
- Commit tiap tugas atau tiap kelompok yang masuk akal, pesan berbahasa Indonesia tanpa jejak alat bantu
- **T007 menahan seluruh keluaran**: konstanta asumsi pemancar belum boleh dipakai menghasilkan ubin sampai rujukannya ditulis. Ini syarat yang tercatat di plan.md, bukan saran
- Berhenti di checkpoint mana pun untuk memeriksa cerita yang sudah jadi

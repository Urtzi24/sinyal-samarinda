# Panduan menjalankan dan memeriksa

**Tanggal:** 2026-08-14

Cara membuktikan Tahap 1 benar-benar jalan, dari repo kosong sampai peta terbuka.
Bukan panduan menulis kodenya — itu ada di `tasks.md`.

---

## Prasyarat

| Yang dibutuhkan | Cara memastikan |
|---|---|
| Python 3.12 | `python --version` |
| `uv` | `uv --version` |
| Node.js | `node --version` |
| Token OpenCelliD | akun gratis di opencellid.org, lalu `OPENCELLID_TOKEN` diisi |

Token bukan penghalang untuk mencoba: `LANGKAH-0.md` memuat cara mengambil salinan
2017 tanpa akun sama sekali. Cukup untuk membuktikan alurnya jalan, terlalu tua
untuk peta yang dipamerkan.

## Urutan pemeriksaan

### 1. Rumus fisikanya benar

**Dijalankan lebih dulu, sebelum ada ubin apa pun.**

```bash
uv run pytest tests/propagation -v
```

**Yang diharapkan:** seluruh tes acuan lolos — keluaran rumus cocok dengan angka
terbitan ITU dalam batas toleransi yang tertulis di tesnya.

**Kalau gagal, berhenti di sini.** Prinsip I melarang menghasilkan ubin dari rumus
yang belum terbukti. Peta yang salah tetap tampak indah, dan tidak akan ada yang
menyadarinya.

### 2. Penyandian ubinnya sepakat dua sisi

```bash
uv run pytest tests/tiles -v
cd etalase && npm test
```

**Yang diharapkan:** ubin contoh yang ditulis Python dibaca TypeScript dan
menghasilkan angka daya yang sama. Kontraknya di
[`contracts/tile-format.md`](contracts/tile-format.md).

### 3. Dapur jalan pada kerincian kasar

```bash
python -m dapur.run semua --kerincian 240
```

**Yang diharapkan:**

- Selesai dalam hitungan **menit**, bukan jam. Kalau berjam-jam pada 240 m, ada
  yang salah — jangan naik ke 30 m.
- Layar menyebut angka di tiap langkah: berapa baris dibuang dan kenapa, berapa
  sel dihitung, berapa ubin per zoom, dan **ukuran total keluaran**.
- `data/keluaran/` berisi tiga arsip sinyal dan satu arsip ketinggian.

**Yang diperiksa dengan mata:**

- Jumlah baris yang dibuang saat `siapkan` masuk akal. Kalau hampir semuanya
  dibuang, pemetaan MNC-nya salah.
- Ukuran keluaran dibandingkan perkiraan 200–350 MB di
  [`research.md`](research.md). Menyimpang jauh berarti perkiraannya salah dan
  harus diperbaiki sekarang, bukan nanti.

### 4. Dapur bisa dilanjutkan

```bash
python -m dapur.run hitung --kerincian 240
# hentikan di tengah dengan Ctrl+C
python -m dapur.run hitung --kerincian 240
```

**Yang diharapkan:** jalan kedua menyebut berapa satuan kerja yang dilewati, dan
selesai jauh lebih cepat. Kalau mengulang dari nol, Prinsip IV dilanggar.

### 5. Peta terbuka dan bisa dipakai

```bash
cd etalase && npm run dev
```

**Yang diharapkan, diperiksa langsung di layar:**

| Yang diperiksa | Kebutuhan |
|---|---|
| Peta terbuka dengan satu operator sudah terpilih, keterangan warna terlihat | FR-009 |
| Menekan tombol operator lain mengubah warna tanpa memuat ulang, posisi peta tidak bergeser | FR-004 |
| Menekan satu titik memunculkan tingkat **dan** nilai teknis, bertanda prediksi | FR-006, FR-022 |
| Peta bisa diputar dan dimiringkan; bukitnya terlihat | FR-002 |
| Daerah tanpa data terlihat **berbeda** dari daerah bersinyal lemah | FR-011 |
| Batasan kejujuran terbaca di halaman | FR-012 |

### 6. Bisa dipakai tanpa peta, dan tanpa tetikus

- Telusuri halaman hanya dengan **Tab** dan **Enter**. Setiap kendali terjangkau,
  posisi fokus terlihat — FR-014.
- Temukan tabel per kecamatan dan baca perkiraan tiap operator tanpa menyentuh
  peta — FR-013.
- Nyalakan pengurangan gerak di setelan sistem, muat ulang: animasinya mati —
  FR-016.

### 7. Jalan di ponsel

Buka dari ponsel kelas menengah, bukan dari peramban laptop yang dikecilkan.

**Yang diharapkan:** panel kendali jadi lembar dari bawah, peta tetap bisa
diputar, kerincian turun otomatis kalau perangkatnya tidak kuat — FR-017, FR-018.

## Ukuran keberhasilan yang tidak bisa diperiksa sendiri

**SC-001** — orang yang belum pernah melihatnya bisa menjawab "operator mana yang
bagus di daerah saya" dalam waktu di bawah satu menit, tanpa dijelaskan.

Ini butuh orang lain. Beri tautannya, sebut satu nama daerah, dan diam. Kalau
harus dijelaskan lebih dulu, petanya belum selesai — dan itu bukan kesalahan yang
bisa ditemukan oleh tes mana pun.

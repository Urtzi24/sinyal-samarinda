# Model Data — Peta Prediksi Sinyal Samarinda (Tahap 1)

**Tanggal:** 2026-08-14

Entitas yang mengalir lewat dapur, dari data mentah sampai ubin siap tampil.
Nama medan berbahasa Inggris sesuai PRD bagian 9; penjelasannya berbahasa
Indonesia.

---

## Transmitter — pemancar

Satu baris OpenCelliD. **Bukan menara fisik** — satu menara memancarkan beberapa
sel, dan posisinya hasil perkiraan.

| Medan | Jenis | Keterangan |
|---|---|---|
| `radio` | teks | `GSM`, `UMTS`, atau `LTE`. Menentukan frekuensi yang diasumsikan |
| `mnc` | bilangan | Kode operator mentah. Dipetakan ke `operator_id` |
| `lon`, `lat` | pecahan | Posisi perkiraan, derajat WGS84 |
| `range` | bilangan | Radius ketidakpastian posisi, meter. Dari OpenCelliD |
| `samples` | bilangan | Jumlah pengukuran yang membentuk perkiraan ini |
| `operator_id` | teks | Hasil pemetaan: `telkomsel`, `ioh`, `xlsmart` |
| `frequency_mhz` | bilangan | **Diasumsikan** dari `radio` |
| `antenna_height_m` | pecahan | **Diasumsikan** |
| `eirp_dbm` | pecahan | **Diasumsikan** |

**Aturan sah:**

- `mcc` wajib 510. Baris lain dibuang saat penyaringan.
- `lon`/`lat` wajib di dalam kotak Samarinda yang dilebihkan **20 km** ke segala
  arah. Pemancar di luar batas kota tetap menyinari kota, jadi tidak boleh
  dipotong tepat di batas administratif.
- `samples` = 0 → baris dibuang. Perkiraan tanpa pengukuran tidak punya dasar.
- `mnc` yang tidak ada di tabel pemetaan → dicatat dan dibuang, tidak diam-diam
  dianggap operator terdekat.

**Pemetaan operator** (dari `LANGKAH-0.md`):

| `operator_id` | Nama tampil | MNC |
|---|---|---|
| `telkomsel` | Telkomsel | 510-10 |
| `ioh` | Indosat Ooredoo Hutchison | 510-01, 510-89 |
| `xlsmart` | XLSmart | 510-11, 510-28 |

## ElevationSurface — permukaan ketinggian

Raster Copernicus DEM GLO-30, satu ubin `S01_00_E117_00`.

| Medan | Jenis | Keterangan |
|---|---|---|
| `elevation_m` | larik pecahan | Ketinggian di atas permukaan laut |
| `transform` | affine | Pemetaan piksel ↔ koordinat bumi |
| `crs` | teks | Sistem koordinat sumber |
| `resolution_m` | pecahan | 30 |

**Aturan sah:** nilai kosong (nodata) wajib dikenali dan **tidak boleh**
diperlakukan sebagai ketinggian nol — laut setinggi nol dan data hilang adalah
dua hal berbeda.

## TerrainProfile — profil medan

Irisan ketinggian sepanjang garis lurus dari satu pemancar ke satu titik hitung.
Masukan untuk perhitungan difraksi. Hidup di memori saja.

| Medan | Jenis | Keterangan |
|---|---|---|
| `distances_m` | larik | Jarak dari pemancar ke tiap titik cuplik |
| `elevations_m` | larik | Ketinggian tanah di tiap titik cuplik |
| `tx_height_m`, `rx_height_m` | pecahan | Tinggi antena di atas tanah, kedua ujung |

**Aturan sah:** pencuplikan wajib serapat DEM (30 m). Mencuplik lebih jarang
melewatkan puncak bukit — dan puncak bukit itulah yang jadi penghalang.

## PredictionCell — sel perkiraan

Satu sel di kisi hitung, untuk satu operator.

| Medan | Jenis | Keterangan |
|---|---|---|
| `lon`, `lat` | pecahan | Titik tengah sel |
| `operator_id` | teks | Operator yang dihitung |
| `received_power_dbm` | pecahan | Hasil akhir: daya terima terkuat dari semua pemancar |
| `data_adequate` | boolean | Ada pemancar terdata yang cukup dekat |
| `inside_city` | boolean | Di dalam batas administratif Kota Samarinda |

**Aturan sah:**

- `received_power_dbm` diambil dari pemancar **terkuat**, bukan dijumlahkan.
  Ponsel menempel ke satu sel, bukan menggabungkan semuanya.
- `data_adequate` = salah kalau tidak ada pemancar operator itu dalam radius yang
  ditetapkan. **Wajib dibedakan dari sinyal lemah** — ini FR-011, dan Langkah 0
  membuktikan ini bukan kasus langka: XLSmart cuma punya 5% data.
- Sel dengan `inside_city` = salah tetap dihitung kalau perlu, tapi ditandai alfa
  0 di ubin.

## SignalTile — ubin sinyal

Satu ubin PNG 256 × 256, untuk satu operator pada satu zoom.

| Medan | Jenis | Keterangan |
|---|---|---|
| `z`, `x`, `y` | bilangan | Alamat ubin, skema Web Mercator |
| `operator_id` | teks | Operator |
| `pixels` | RGBA | Penyandiannya di [`contracts/tile-format.md`](contracts/tile-format.md) |

**Aturan sah:** ubin yang sudah ada di cakram dilewati saat dapur dijalankan
ulang — ini yang memenuhi Prinsip IV.

## AdministrativeArea — wilayah administratif

Kecamatan dan kelurahan Kota Samarinda. Dipakai untuk label peta (FR-010) dan
untuk jalur baca tanpa peta (FR-013).

| Medan | Jenis | Keterangan |
|---|---|---|
| `name` | teks | Nama kecamatan atau kelurahan |
| `level` | teks | `kecamatan` atau `kelurahan` |
| `geometry` | poligon | Batas wilayah |

**Aturan sah:** nama wilayah di OpenStreetMap **tidak selalu memakai awalan
"Kota"** — Kota Samarinda tersimpan sebagai `Samarinda` saja. Pencarian
berdasarkan nama wajib diuji terhadap kontrol yang hasilnya sudah diketahui,
karena nama yang salah mengembalikan nol tanpa pesan galat. Jebakan ini sudah
memakan satu kali di Langkah 0.

---

## Alur antar entitas

```text
Transmitter ─┐
             ├─→ TerrainProfile ─→ PredictionCell ─→ SignalTile ─→ PMTiles
ElevationSurface ─┘                                      ↑
                                    AdministrativeArea ──┘
                                    (batas kota → kanal alfa)
```

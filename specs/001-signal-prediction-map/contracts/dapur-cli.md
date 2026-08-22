# Kontrak: perintah dapur

**Antara:** orang yang menjalankan dapur ↔ `dapur/run.py`

Dapur dijalankan dengan tangan, sesekali, saat data diperbarui. Bukan layanan,
bukan dipicu saat halaman dibuka.

---

## Perintah

```bash
python -m dapur.run <langkah> [pilihan]
```

| Langkah | Kerjanya | Menyentuh jaringan |
|---|---|---|
| `unduh` | Ambil data pemancar dan ubin ketinggian ke `data/mentah/` | ya |
| `siapkan` | Saring ke Samarinda, petakan MNC ke operator, buang baris tidak sah | tidak |
| `hitung` | Hitung daya terima seluruh kisi, per operator | tidak |
| `ubin` | Sandikan ke PNG, bungkus jadi PMTiles di `data/keluaran/` | tidak |
| `semua` | Keempatnya berurutan | ya |

## Pilihan

| Pilihan | Bawaan | Gunanya |
|---|---|---|
| `--kerincian <meter>` | `240` | Ukuran sel hitung. `240` untuk mencoba, `30` untuk keluaran sebenarnya |
| `--operator <id>` | semua | Batasi ke satu operator: `telkomsel`, `ioh`, `xlsmart` |
| `--zoom <a>-<b>` | `10-16` | Jangkauan zoom ubin |
| `--paksa-ulang` | mati | Hitung ulang semuanya, abaikan hasil yang sudah ada |

## Aturan yang mengikat

1. **Bisa dilanjutkan, bukan diulang dari nol.** Tanpa `--paksa-ulang`, setiap
   langkah melewati satuan kerja yang keluarannya sudah ada di cakram. Berhenti
   di tengah lalu dijalankan lagi harus melanjutkan. Ini Prinsip IV, dan
   perhitungan seluruh kota terlalu lama untuk diulang gara-gara laptop tidur.

2. **Menjalankan ulang penuh menghasilkan keluaran yang sama.** Tidak ada jam
   sistem, tidak ada keacakan tanpa benih tetap.

3. **Hanya `unduh` yang boleh menyentuh jaringan.** `siapkan`, `hitung`, dan
   `ubin` wajib jalan tanpa internet. Ini yang menjaga Prinsip III tetap bisa
   ditegakkan — kalau perhitungan boleh mengunduh, matematikanya tidak lagi murni.

4. **Token OpenCelliD dibaca dari variabel lingkungan `OPENCELLID_TOKEN`.**
   Kalau kosong, `unduh` berhenti dengan pesan yang menyebut nama variabelnya dan
   cara mendapatkannya. Dilarang ada token contoh di dalam kode, dan dilarang
   gagal diam-diam.

5. **Data mentah tidak pernah masuk git.** `data/` sudah diabaikan. Yang masuk
   git adalah perintah ini beserta kodenya — Prinsip V.

## Keluaran

```text
data/
├── mentah/
│   ├── cell_towers.csv.gz
│   └── samarinda_dem.tif
├── antara/
│   ├── pemancar-samarinda.csv        # hasil `siapkan`
│   └── kisi-{operator}-{kerincian}m.npy   # hasil `hitung`
└── keluaran/
    ├── sinyal-telkomsel.pmtiles
    ├── sinyal-ioh.pmtiles
    ├── sinyal-xlsmart.pmtiles
    └── ketinggian.pmtiles
```

Berkas di `antara/` yang membuat langkah bisa dilanjutkan. Berkas di `keluaran/`
yang diunggah.

## Yang wajib dilaporkan ke layar

Setiap langkah menyebut angka, bukan cuma "selesai":

- `unduh` — ukuran tiap berkas yang diambil
- `siapkan` — berapa baris masuk, berapa dibuang, dan **alasannya per golongan**
- `hitung` — jumlah sel, waktu yang dipakai, berapa yang dilewati karena sudah ada
- `ubin` — jumlah ubin per zoom, dan **ukuran total keluaran**

Angka terakhir itu penting: PRD bagian 12 menyebut ukuran keluaran sebagai risiko,
dan riset Phase 0 memperkirakannya 200–350 MB. Perkiraan itu wajib dibandingkan
dengan kenyataan sejak putaran pertama, bukan di akhir.

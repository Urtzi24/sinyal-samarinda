# Langkah 0 — pemeriksaan nyawa proyek

**Dijalankan:** 14 Agustus 2026
**Putusan gerbang:** **LOLOS, dengan tiga catatan yang mengubah PRD**

Seluruh rancangan Sinyal Samarinda berdiri di atas satu asumsi: data posisi
menara BTS Samarinda tersedia terbuka dan bisa dipisahkan per operator. Dokumen
ini menguji asumsi itu dengan data sungguhan, bukan dengan membaca klaim.

Rinciannya di [`PRD.md`](PRD.md) bagian 4.

---

## Hasil per syarat

### Syarat 1 — data menara bisa diunduh, jumlahnya masuk akal

**LOLOS.**

Sumber: cermin basis data OpenCelliD di Internet Archive, `cell_towers.csv.gz`,
707 MB, terbitan 2017, lisensi CC BY-SA 3.0. Bisa diambil **tanpa akun dan tanpa
kunci API**.

Disaring ke kotak batas Samarinda (117,00–117,35 BT; 0,28–0,75 LS):

| | Jumlah |
|---|---|
| Baris sel | 8.937 |
| Titik lokasi berbeda (dibulatkan ~100 m) | ~3.757 |

Sebaran jenis jaringan: UMTS 6.454, GSM 2.262, LTE 221.

**Angka ~3.757 titik jangan dibaca sebagai jumlah menara fisik.** OpenCelliD
menyimpan posisi *sel* hasil perkiraan dari pengukuran ponsel orang banyak, dan
perkiraan untuk satu menara yang sama bisa berserak puluhan sampai ratusan meter.
Jumlah menara sesungguhnya hampir pasti jauh lebih kecil — kemungkinan ratusan.
Untuk pertanyaan gerbang ini ("apakah ada bahan yang cukup?") jawabannya tetap ya.

### Syarat 2 — tiap menara bisa dikenali operatornya

**LOLOS.**

Struktur berkas: `radio,mcc,net,area,cell,unit,lon,lat,range,samples,changeable,created,updated,averageSignal`

Kolom `net` adalah MNC — kode operator. Indonesia memakai MCC 510. Tiap baris
membawa identitas operatornya sendiri, jadi pemisahan per operator tidak perlu
ditebak.

Sebaran di Samarinda menurut kode 2017:

| MNC | Operator (2017) | Sel | Bagian |
|---|---|---|---|
| 510-10 | Telkomsel | 6.830 | 76,4% |
| 510-01 | Indosat | 936 | 10,5% |
| 510-89 | Tri (Hutchison) | 710 | 7,9% |
| 510-11 | XL Axiata | 456 | 5,1% |
| 510-28 | Smartfren | 5 | 0,1% |

### Syarat 3 — data ketinggian tanah tersedia dengan kerincian memadai

**LOLOS.**

Kotak batas Kota Samarinda: 0,3144–0,7168 LS; 117,0540–117,2982 BT — kira-kira
27 km (barat–timur) × 45 km (utara–selatan). Seluruhnya muat dalam **satu ubin**
DEM 1° × 1°.

Sumber terpilih: **Copernicus DEM GLO-30**, resolusi 30 m, ubin
`Copernicus_DSM_COG_10_S01_00_E117_00_DEM`, 23 MB. Diverifikasi langsung: HTTP
200, tanpa akun, tanpa kunci, melayani permintaan sebagian, dan tanda tangan
berkasnya memang Cloud-Optimized GeoTIFF yang sah.

Resolusi 30 m adalah masukan baku untuk perkakas propagasi radio, jadi memadai.
**DEMNAS** milik Badan Informasi Geospasial lebih halus (8 m) dan akan lebih baik
untuk kota berbukit seperti Samarinda, tapi unduhannya mensyaratkan pengisian
identitas surel. Ditandai sebagai peningkatan opsional, bukan penghalang.

---

## Sumber yang ditolak

**OpenStreetMap.** Diuji lebih dulu karena bisa diambil tanpa akun sama sekali.
Hasilnya di seluruh Kota Samarinda: 12 tiang komunikasi, 3 menara umum, dan
**nol** yang punya tag operator. Kontrol dengan objek lain di wilayah yang sama
menghasilkan 528 sekolah — jadi Samarinda memang terpetakan di OSM; menaranya
saja yang tidak. Gagal di syarat 1 maupun syarat 2.

---

## Tiga catatan yang mengubah PRD

### 1. Operatornya sekarang tiga, bukan lima

Data 2017 memuat lima operator. Sejak itu terjadi dua penggabungan:

- **Indosat Ooredoo Hutchison** — Indosat dan Tri bergabung, 2022.
- **XLSmart** — XL Axiata, Smartfren, dan Smart Telecom bergabung, resmi
  beroperasi 16 April 2025.

Jadi pada 2026 pilihan operator di peta seharusnya **tiga**, dan kode MNC lama
harus dikelompokkan:

| Operator 2026 | MNC yang digabung | Sel di data 2017 | Bagian |
|---|---|---|---|
| Telkomsel | 510-10 | 6.830 | 76,4% |
| Indosat Ooredoo Hutchison | 510-01, 510-89 | 1.646 | 18,4% |
| XLSmart | 510-11, 510-28 | 461 | 5,2% |

Ini mengenai keputusan terkunci "Dibedakan per operator" di PRD bagian 14.
Keputusannya tetap sah — jumlah pilihannya yang berubah.

### 2. Ketimpangan datanya parah, dan itu bisa menyesatkan

Telkomsel memegang 76% data; XLSmart cuma 5%. Kalau tidak ditangani, peta akan
menampilkan XLSmart seolah sinyalnya buruk di mana-mana — padahal yang terjadi
adalah menaranya tidak terdata.

Spesifikasi sudah mengantisipasi ini di FR-011 dan di kasus tepi, tapi sekarang
ada angkanya. Ini bukan risiko teoretis lagi.

### 3. "Posisi menara" sebenarnya "posisi sel yang diperkirakan"

PRD bagian 1 menulis perkiraannya "dihitung dari posisi menara BTS". Lebih tepat:
dihitung dari **posisi sel hasil perkiraan orang banyak**. Selisih ini nyata dan
memengaruhi ketelitian, jadi layak masuk daftar batasan jujur di PRD bagian 7.

---

## Yang belum diselesaikan

- **Data terkini butuh akun OpenCelliD.** Yang dipakai di sini terbitan 2017 dan
  berlaku sebagai batas bawah — 2017 adalah masa awal 4G, terlihat dari LTE yang
  cuma 2,5%. Data sekarang pasti jauh lebih padat dan lebih merata. Unduhan
  terkini mensyaratkan akun gratis di opencellid.org; **pendaftarannya harus
  dikerjakan Ali sendiri.**
- **DEMNAS 8 m** perlu pengisian identitas surel di tanahair.indonesia.go.id.
  Juga harus dikerjakan Ali sendiri kalau mau dipakai.
- **Jumlah menara fisik sebenarnya belum diketahui.** Perlu penggabungan sel yang
  lebih pintar daripada pembulatan 100 m yang dipakai di sini.

---

## Cara mengulang pemeriksaan ini

Sesuai Prinsip V, data mentahnya tidak masuk git — perintahnya yang masuk.

Jumlah dan sebaran sel Samarinda dari cermin OpenCelliD:

```bash
curl -sL "https://archive.org/download/opencellid_cell_towers.csv/cell_towers.csv.gz" \
  | gunzip -c \
  | awk -F, 'NR>1 && $2==510 && $7>=117.00 && $7<=117.35 && $8>=-0.75 && $8<=-0.28' \
  > data/samarinda_cells.csv
```

Ubin ketinggian Samarinda:

```bash
curl -L -o data/samarinda_dem.tif \
  "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S01_00_E117_00_DEM/Copernicus_DSM_COG_10_S01_00_E117_00_DEM.tif"
```

Menara di OpenStreetMap — pemeriksaan yang menghasilkan penolakan:

```bash
curl -s -G "https://overpass-api.de/api/interpreter" --data-urlencode 'data=[out:json][timeout:110];
area(3614921097)->.a;
(nwr["man_made"="mast"](area.a); nwr["man_made"="tower"](area.a););
out tags center;'
```

`3614921097` adalah area OSM untuk Kota Samarinda. Namanya di OSM cuma
**"Samarinda"** — bukan "Kota Samarinda". Kueri dengan nama yang salah
mengembalikan nol tanpa pesan galat, dan itu terbaca persis seperti "tidak ada
data".

# Riset Phase 0 — Peta Prediksi Sinyal Samarinda (Tahap 1)

**Tanggal:** 2026-08-14

Yang belum terjawab sebelum rencana ini disusun, dan bagaimana masing-masing
diselesaikan. Sumber data sudah ditetapkan di [`LANGKAH-0.md`](../../docs/LANGKAH-0.md)
dan tidak diulang di sini.

---

## 1. Model propagasi mana yang dipakai

**Keputusan:** bertahap. **Tahap A** — ruang bebas + difraksi medan menurut
**ITU-R P.526** (metode mata pisau, penggabungan Deygout). **Tahap B** — naik ke
**ITU-R P.1812** setelah seluruh alur terbukti jalan.

**Alasan:**

Difraksi medan **tidak bisa ditawar**. Tujuan kedua di PRD bagian 3 berbunyi
"menunjukkan sebabnya" — permukaan 3D harus memperlihatkan bahwa suatu daerah
merah karena terhalang bukit tertentu. Model empiris murni seperti Hata atau
COST-231 tidak tahu apa-apa soal bukit; memakainya berarti membuang alasan
proyek ini ada.

P.526 dipilih untuk memulai karena bagian difraksinya bisa ditulis dan diuji
sendiri dalam ukuran yang wajar, sementara P.1812 adalah rekomendasi utuh dengan
banyak sub-model. Menulis P.1812 lengkap lebih dulu adalah cara paling rapi untuk
menabrak risiko "proyek terlalu besar lalu ditinggalkan" di PRD bagian 12.
Pentahapan ini juga persis yang diminta PRD bagian 5: mulai kasar, buktikan
alurnya, baru perhalus.

**Alternatif yang ditimbang:**

- **Longley-Rice (ITM)** — punya implementasi Python (`itmlogic`, `pyitm`) dan
  tervalidasi terhadap kumpulan contoh NTIA 82-100. Ditolak untuk permulaan
  karena rancangannya titik-ke-titik, sedangkan yang dibutuhkan titik-ke-wilayah,
  dan modelnya lebih tua dari P.1812.
- **Hata / COST-231 saja** — ditolak: tanpa difraksi medan, tidak menjelaskan
  sebab.
- **Memakai pustaka jadi (`Py1812`, `itmlogic`) alih-alih menulis sendiri** —
  ditolak. PRD bagian 8 sudah menetapkan pembagiannya: yang sudah dipecahkan
  ribuan orang boleh dipinjam, tapi mesin prediksinya justru bagian yang
  sengaja dibangun sendiri. Itu yang membuat pertanyaan "ini kamu hitung
  sendiri?" punya jawaban.

## 2. Dari mana angka acuan untuk tes

**Keputusan:** data validasi resmi ITU.

**Alasan:** Prinsip I mewajibkan tiap rumus fisika punya tes berangka acuan dari
sumber yang hasilnya sudah diketahui. Keduanya menyediakan:

- **ITU-R P.526** — contoh perhitungan difraksi dengan nilai terbitan di teks
  rekomendasinya sendiri.
- **ITU-R P.1812** — menerbitkan berkas profil medan beserta keluaran yang
  diharapkan, khusus untuk memvalidasi implementasi perangkat lunak. Ini yang
  membuat Tahap B bisa diuji dengan benar, bukan diuji terhadap dirinya sendiri.

**Konsekuensi yang mengikat:** rumus tanpa tes acuan dilarang dipakai
menghasilkan ubin yang diunggah. Tes ditulis lebih dulu.

## 3. Parameter pemancar yang tidak ada di data

**Ini lubang terbesar di seluruh rencana, dan tidak bisa ditutup.**

OpenCelliD menyimpan `radio`, `lon`, `lat`, `range`, dan `samples`. Yang
dibutuhkan rumus propagasi tapi **tidak ada**: frekuensi, tinggi antena, daya
pancar, arah dan kemiringan antena.

**Keputusan:** diasumsikan, dan tiap asumsi jadi konstanta bernama dengan sumber
tertulis di komentar — Prinsip II.

**Sumber utama:** Report ITU-R M.2292-0 (12/2013), *Characteristics of
terrestrial IMT-Advanced systems for frequency sharing/interference analyses*,
Tabel 2 (pita di bawah 1 GHz) dan Tabel 3 (pita 1–3 GHz), kolom **Macro urban**.

| Jenis radio | Frekuensi | Tinggi antena | EIRP/sektor | Dasar |
|---|---|---|---|---|
| GSM | 900 MHz | 30 m | 58 dBm / 10 MHz | M.2292 Tabel 2 |
| LTE | 1800 MHz | 25 m | 59 dBm / 10 MHz | M.2292 Tabel 3, baris 1–2 GHz |
| UMTS | 2100 MHz | 20 m | 59 dBm / 10 MHz | M.2292 Tabel 3, baris 2–3 GHz |

| Parameter lain | Nilai | Dasar |
|---|---|---|
| Tinggi penerima | 1,5 m | 3GPP TR 38.901, skenario Urban Macro |
| Arah antena | menyebar rata (omni) | Arah sektor tidak diketahui; mengarang arah lebih buruk daripada mengabaikannya |

EIRP di tabel itu **sudah termasuk** gain antena dan rugi feeder, jadi keduanya
tidak dihitung lagi terpisah. Angka penyusunnya: daya keluaran 46 dBm dalam
10 MHz, gain antena maksimum 16 dBi (15 dBi untuk pita di bawah 1 GHz), rugi
feeder 3 dB.

**Pemetaan frekuensi adalah pilihan, bukan fakta.** Tiap teknologi dipakai di
lebih dari satu pita di Indonesia; yang dipilih adalah pita tempat teknologi itu
paling banyak digelar. Ini yang paling layak diganti pertama kalau nanti ada data
yang menyebut pita sebenarnya per sel — redaman ruang bebas naik 20 log₁₀(f),
jadi selisih 900 dan 1800 MHz saja sudah 6 dB.

**Satu keringanan yang layak dicatat.** Karena asumsi ini seragam untuk semua
pemancar, EIRP bekerja sebagai geseran tetap: ia menggeser seluruh peta naik atau
turun bersama-sama tanpa mengubah pola relatifnya. Artinya pertanyaan utama —
"operator mana yang lebih baik di daerah saya" — jauh lebih tahan terhadap
kesalahan angka ini daripada nilai dBm yang ditampilkan saat titik ditekan.
Ketepatan mutlak dan ketepatan relatif tidak sama-sama rapuh di sini.

**Akibat yang harus ditampilkan di peta:** asumsi ini kemungkinan menyumbang
kesalahan lebih besar daripada modelnya sendiri. Menganggap semua pemancar sama
tinggi dan sama kuat berarti perbedaan antar lokasi datang hampir seluruhnya dari
jarak dan medan. Ini batasan baru yang belum ada di PRD bagian 7.

## 4. Cara menyandikan nilai sinyal ke RGB

**Keputusan:** 16 bit di kanal merah–hijau, kanal biru untuk kecukupan data,
kanal alfa untuk batas kota.

| Kanal | Isi |
|---|---|
| R, G | nilai 16 bit = `(dBm + 140) × 10`, jangkauan −140…+40 dBm, langkah 0,1 dB |
| B | kecukupan data: 0 = tidak memadai, >0 = memadai |
| A | 0 = di luar batas Kota Samarinda, 255 = di dalam |

**Alasan:** PRD sudah mengunci "nilai disandikan ke RGB, bukan warna jadi",
supaya skema warna bisa diganti tanpa menghitung ulang berjam-jam. Menaruh
kecukupan data di kanal biru menyelesaikan **FR-011** tanpa berkas kedua — peramban
bisa membedakan "sinyal lemah" dari "tidak terdata" dari piksel yang sama. Kanal
alfa menyelesaikan kasus tepi "titik di luar batas kota".

Langkah 0,1 dB jauh lebih halus daripada ketelitian modelnya. Itu disengaja:
penyandian tidak boleh jadi sumber galat tambahan, sedangkan **yang ditampilkan
ke pengguna tetap dibulatkan** — peta tidak boleh memamerkan ketelitian yang tidak
dimilikinya.

## 5. Kerincian hitung dan jangkauan zoom

**Keputusan:** mulai 240 m, naik ke 30 m menyamai DEM. Ubin zoom 10–16.

| Kerincian | Sel per operator | Gunanya |
|---|---|---|
| 240 m (8× DEM) | ~21.000 | membuktikan seluruh alur jalan, iterasi hitungan menit |
| 30 m (setara DEM) | ~1.350.000 | keluaran sebenarnya |

### Yang terukur, 15 Agustus 2026

Perkiraan jumlah selnya tepat: **1.343.598 sel** pada 30 m, meleset 0,5% dari
taksiran 1.350.000.

| Kerincian | Sel | Waktu hitung, tiga operator |
|---|---|---|
| 240 m | 21.000 | 176 detik |
| 60 m | 336.126 | 21 menit |
| 30 m | 1.343.598 | **95 menit** (1.813 + 1.903 + 1.999 detik) |

Waktunya naik sebanding dengan jumlah sel, bukan lebih cepat dari itu: 4× sel
dari 60 m ke 30 m menghasilkan 4,5× waktu. Artinya penyaring delapan pemancar
teratas bekerja seperti maksudnya — biaya per sel tetap kira-kira sama berapa
pun rapatnya kisi.

Kelengkapan data pada 30 m, dan inilah alasan FR-011 wajib ada:

| Operator | Sel terdata | Bagian kota |
|---|---|---|
| Telkomsel | 1.278.621 | 95,2% |
| Indosat | 1.204.202 | 89,6% |
| XLSmart | 870.689 | **64,8%** |

Sepertiga Samarinda tidak punya data XLSmart sama sekali. Tanpa pembedaan
"tidak terdata" dari "sinyal lemah", operator itu akan terbaca buruk di
sepertiga kota padahal yang terjadi menaranya tidak terdaftar.

### Zoom di atas z13 tidak menambah keterangan apa pun

Diukur, bukan diperkirakan. Satu piksel di khatulistiwa:

| Zoom | Meter per piksel |
|---|---|
| z12 | 38,22 |
| **z13** | **19,11** |
| z14 | 9,55 |
| z15 | 4,78 |
| z16 | 2,39 |

Kisi 30 m setara zoom **12,35**. Jadi z14 ke atas seluruhnya hasil sisipan,
bukan pengukuran — dan menurut tabel jumlah ubin di bawah, z14–z16 memikul 98%
dari seluruh ubin.

Itu **tidak** berarti zoom tinggi harus dibuang. Ubin dicuplik dwilinear dari
kisi lebih dulu, jadi batas antar tingkat warna tetap tajam di zoom berapa pun.
Kalau zoom maksimum diturunkan dan MapLibre yang membesarkan sendiri, yang
dibesarkan adalah gambar yang sudah diwarnai — batas tingkatnya jadi kabur
melebur, persis gradasi mulus yang PRD bagian 10 tolak. Ongkos ukuran ditukar
dengan ketajaman yang memang disengaja.

Perkiraan jumlah ubin untuk kotak Samarinda (0,2442° × 0,4024°):

| Zoom | Ubin, perkiraan | Ubin, terukur |
|---|---|---|
| 16 | ~3.330 | tidak dibuat |
| 15 | ~851 | 558 |
| 14 | ~228 | 158 |
| 10–13 | ~83 | 79 |
| **Total per operator** | **~4.500** | **795** |

**Perkiraan ukuran keluaran: 200–350 MB.** **Terukur: 124 MB.**

### Kenapa perkiraannya meleset 2,8×

Bukan karena ubinnya lebih kecil dari dugaan, melainkan karena **zoom 16 tidak
pernah dibuat**. Perkiraan itu menghitung z16 sebagai 74% dari seluruh ubin;
setelah diukur, zoom 30 m setara z12,35, jadi z16 akan berisi empat kali lipat
ubin yang seluruhnya sisipan dari sisipan. Zoom maksimum ditutup di 15.

Sisa selisihnya karena perkiraan ubinnya sendiri kelebihan sekitar 35% — kotak
batas Samarinda tidak persegi, jadi sebagian ubin di sudut kotak jatuh
seluruhnya di luar kota dan tidak ditulis sama sekali.

Ukuran terukur, 15 Agustus 2026, kerincian 30 m, zoom 10–15:

| Berkas | Zoom | MB |
|---|---|---|
| `sinyal-xlsmart.pmtiles` | 10–15 | 32,7 |
| `sinyal-ioh.pmtiles` | 10–15 | 31,5 |
| `sinyal-telkomsel.pmtiles` | 10–15 | 30,2 |
| `ketinggian.pmtiles` | 10–15 | 17,3 |
| `kota.pmtiles` | 10–16 | 12,0 |
| geojson dan json kecil | — | 0,5 |
| **Total** | | **124,3** |

Berkas terbesar **32,7 MB**. Angka itu yang menentukan tempat unggah, bukan
totalnya — lihat bagian 8.

Menaikkan kerincian dari 60 m ke 30 m menambah **25%** ukuran pada jangkauan
zoom yang sama (75,5 MB jadi 94,4 MB untuk tiga arsip sinyal). Datanya empat
kali lebih rapat, tapi ubinnya sama banyak; yang bertambah cuma rincian yang
membuat PNG-nya lebih sulit dimampatkan.

**Ini menutup satu risiko di PRD bagian 12.** "Ukuran berkas ubin melebihi batas
hosting gratis" tidak terjadi, dan sekarang terbukti dengan angka, bukan
perkiraan: 124 MB lawan 10 GB paket gratis Cloudflare R2 — 80 kali lebih besar
dari kebutuhan.

## 6. Dua pustaka tambahan di luar PRD bagian 9

**Keputusan:** `Pillow` untuk menulis PNG, `pmtiles` untuk membungkus arsip.

**Alasan:** PRD bagian 9 mengizinkan penambahan asal ada alasannya. Menulis
penyandi PNG dan format arsip PMTiles dari nol adalah pekerjaan yang sudah selesai
di tempat lain dan tidak menyumbang apa pun ke nilai proyek — persis pertimbangan
yang dipakai PRD bagian 8 saat memilih MapLibre daripada Three.js.

**Catatan kematangan:** paket `pmtiles` Python masih berstatus beta. Cadangannya
`rio-pmtiles` (pengaya rasterio, sudah ada di daftar PRD). Diputuskan saat menulis
kode, bukan sekarang.

## 7. Token OpenCelliD

**Keputusan:** lewat variabel lingkungan, tidak pernah masuk git.

**Alasan:** Prinsip VII melarang **kunci berbayar**. Token OpenCelliD gratis, jadi
tidak melanggar. Tapi kunci apa pun yang bocor ke repo adalah cacat tersendiri,
dan repo ini akan dilihat pemberi kerja.

**Konsekuensi:** skrip pengunduh harus gagal dengan pesan yang jelas kalau token
tidak ada — bukan gagal diam-diam, dan bukan menyelipkan token contoh ke kode.

## 8. Tempat unggah

**Diperiksa 15 Agustus 2026, setelah ukuran sebenarnya diketahui.**

PMTiles menuntut satu hal yang tidak semua tempat penyimpanan punya: **HTTP
Range Request**. Seluruh gunanya format ini adalah peramban mengambil potongan
arsip yang sedang dilihat, bukan seluruh 32 MB-nya. Tanpa itu, tiap pengunjung
mengunduh 124 MB untuk melihat satu layar.

Yang menyaring pilihan bukan totalnya, melainkan **berkas terbesar, 32,7 MB**.

| Tempat | Batas per berkas | Batas situs | Muat? |
|---|---|---|---|
| Cloudflare R2 | tidak ada yang relevan | 10 GB gratis | ya |
| GitHub Pages | — | 1 GB, lalu lintas 100 GB/bulan | ya |
| Cloudflare Pages | **25 MiB** | 20.000 berkas | **tidak** |

**Cloudflare Pages gugur karena angka, bukan selera.** Batas 25 MiB (26,2 MB)
per aset lebih kecil daripada arsip sinyal mana pun. Ini juga sebabnya arsip
tidak boleh digabung jadi satu — memisahnya per operator bukan cuma soal rapi.

**Yang direkomendasikan: Cloudflare R2 untuk ubinnya.** Penyimpanan 10 GB dan
**egress gratis** — tidak ada tagihan lalu lintas, berapa pun yang membuka. Ia
juga tempat yang direkomendasikan pembuat format PMTiles sendiri, persis karena
alasan itu. Perlu akun Cloudflare, dan biasanya perlu kartu terdaftar walau
paket gratisnya tidak menagih.

**Cadangannya: GitHub Pages.** Tidak perlu akun baru sama sekali, dan 124 MB
muat di bawah 1 GB. Ongkosnya nyata dan permanen: 124 MB ubin harus masuk git,
tinggal di riwayatnya selamanya, dan ikut terunduh tiap kali repo di-clone. Itu
bertabrakan dengan Prinsip V — data mentah dan hasil hitung di luar git — walau
ubin secara harfiah keluaran, bukan data mentah.

**Belum dieksekusi.** Membuat akun dan mendaftarkan kartu adalah keputusan Ali,
bukan keputusan yang boleh diambilkan.

---

## Yang sengaja belum diputuskan
- **Numba.** PRD melarang memakainya sebelum NumPy terbukti lambat lewat
  pengukuran. Belum ada pengukuran, jadi belum ada bahasan.
- **Penggabungan sel jadi menara fisik.** Tercatat sebagai pekerjaan terbuka di
  `LANGKAH-0.md`. Tahap A boleh menghitung per sel; penggabungan adalah
  penghalusan, bukan syarat.

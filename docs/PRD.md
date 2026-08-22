# PRD — Sinyal Samarinda

**Status:** disepakati, belum ada kode
**Ditulis:** 14 Agustus 2026

Dokumen ini sumber kebenaran tentang *apa* yang dibangun dan *kenapa*. Cara
membangunnya ada di rencana implementasi terpisah. Kalau kode dan dokumen ini
bertentangan, salah satunya harus diperbaiki — jangan dibiarkan.

---

## 1. Ringkasan

Peta 3D bentang alam Kota Samarinda yang menampilkan perkiraan kualitas sinyal
tiap operator seluler di setiap titik kota, dan menjadi lebih akurat seiring
orang memakainya.

Perkiraannya bukan tebakan: dihitung dari posisi pemancar seluler dan bentuk
permukaan tanah, memakai rumus propagasi radio — termasuk memperhitungkan
bukit yang menghalangi sinyal.

Satu catatan ketelitian sejak kalimat pertama: posisi pemancar yang dipakai
berasal dari basis data terbuka yang isinya **perkiraan letak sel**, dikumpulkan
dari pengukuran ponsel orang banyak — bukan koordinat menara hasil survei.
Selisihnya dijelaskan di bagian 7.

## 2. Masalah yang dijawab

Orang di Samarinda tidak punya cara menjawab pertanyaan sederhana ini:

> "Saya mau pindah kos/rumah/kantor ke daerah X. Operator mana yang sinyalnya
> bagus di sana?"

Peta cakupan resmi dari operator dibuat oleh pihak yang berkepentingan menjual,
cakupannya kasar, dan tidak bisa dibandingkan antar-operator dalam satu layar.

**Untuk siapa:** orang yang akan pindah tempat tinggal atau usaha di Samarinda,
dan siapa pun yang penasaran kenapa sinyal di daerahnya jelek.

## 3. Tujuan

1. Menjawab pertanyaan di atas dalam satu layar, tanpa perlu daftar akun.
2. Menunjukkan **sebabnya**, bukan cuma hasilnya — permukaan 3D membuat orang
   melihat bahwa daerahnya merah karena terhalang bukit tertentu.
3. Menjadi bukti kemampuan teknis yang tidak bisa disalin dari tutorial.

### Bukan tujuan

Tidak dibuat, dan penolakannya disengaja:

| Yang ditolak | Alasan |
|---|---|
| Akun & login | Tidak ada yang perlu disimpan per orang. Menambah kerja tanpa menambah nilai. |
| Aplikasi HP | Menghalangi orang mencoba. Cukup kirim link. |
| Kota selain Samarinda | Satu kota yang tergarap benar lebih meyakinkan daripada lima kota setengah jadi. |
| Rekomendasi "beli kartu merek X" | Peta cukup menampilkan data biar orang menyimpulkan sendiri. Begitu menyarankan merek, muncul tanggung jawab kalau orang kecewa padahal datanya masih prediksi. |
| Prediksi kondisi masa depan | Di luar kemampuan data yang ada. |

## 4. Langkah 0 — pemeriksaan nyawa proyek

**Dikerjakan sebelum baris kode produksi mana pun ditulis.**

Seluruh rancangan ini berdiri di atas satu asumsi: data posisi menara BTS
Samarinda tersedia terbuka dan bisa dipisahkan per operator. Kalau asumsi itu
salah, mesin prediksi tidak punya bahan dan rancangan ini harus dirombak.

Yang harus dibuktikan:

1. Data menara Samarinda bisa diunduh, dan jumlahnya masuk akal untuk kota
   sebesar ini.
2. Tiap menara bisa dikenali operatornya.
3. Data ketinggian tanah Samarinda bisa diunduh dengan kerincian yang memadai.

**Gerbang keputusan:** kalau ketiganya lolos, lanjut ke Tahap 1. Kalau tidak,
berhenti dan rancang ulang di sesi itu juga — jangan menulis kode di atas
fondasi yang belum terbukti.

**Sudah dijalankan 14 Agustus 2026. Ketiganya lolos.** Angka lengkap, sumber yang
dipakai, sumber yang ditolak, dan perintah untuk mengulang pemeriksaannya ada di
[`LANGKAH-0.md`](LANGKAH-0.md). Tiga temuan dari pemeriksaan itu sudah dituangkan
ke bagian 1, 7, dan 14 dokumen ini.

## 5. Tahap 1 — mesin prediksi

Inti proyek. Ini yang harus selesai lebih dulu dan berdiri sendiri.

**Definisi selesai:**

- Siapa pun membuka link, melihat Samarinda sebagai permukaan 3D sesuai
  ketinggian aslinya.
- Bisa memilih operator; warna di permukaan berubah menampilkan perkiraan
  kualitas sinyal.
- Bisa diputar, dimiringkan, di-zoom dengan lancar.
- Mencakup seluruh wilayah Kota Samarinda.
- Batasan dan tingkat ketidakpastian tertulis di halaman itu sendiri.

**Tidak ada server yang menghitung apa pun saat halaman dibuka.** Semua
perhitungan sudah dikerjakan lebih dulu di laptop dan hasilnya diunggah sebagai
berkas jadi.

**Kerincian perhitungan:** mulai dari kotak kasar untuk membuktikan seluruh
alurnya jalan, lalu diperhalus bertahap. Memulai langsung dari kerincian
tertinggi berisiko menghabiskan berjam-jam sebelum ketahuan alurnya salah.

## 6. Tahap 2 — lapisan koreksi

Baru dikerjakan setelah Tahap 1 benar-benar selesai dan bisa dipamerkan.

Pengunjung menekan tombol "ukur di sini". Browser mengukur kecepatan dan
kelambatan internet di lokasinya, mengirim hasilnya, lalu sistem
membandingkannya dengan prediksi dan menyesuaikan perkiraan di wilayah itu.

Peta memperbaiki dirinya sendiri seiring dipakai. Ini yang membuat proyek
"dipakai orang", bukan sekadar "dilihat orang".

**Yang harus dipikirkan sejak awal Tahap 2:** kiriman tanpa akun bisa
disalahgunakan. Perlu pembatasan laju kiriman dan penolakan data yang
menyimpang jauh.

## 7. Batasan jujur

Ditulis di sini supaya tidak ada yang lupa, dan **wajib ditampilkan juga di
petanya sendiri**:

1. **Browser tidak bisa membaca kekuatan sinyal seluler (dBm).** Itu hanya bisa
   dilakukan aplikasi HP. Maka yang diukur di Tahap 2 adalah *kecepatan
   internet yang dirasakan*, bukan kekuatan sinyal mentah. Keduanya
   berhubungan, tapi tidak sama.
2. **Ini prediksi, bukan pengukuran.** Rumus propagasi tidak tahu ada gedung
   baru, menara yang sedang mati, atau jaringan yang sedang padat.
3. **Data menara terbuka tidak pernah lengkap, dan bolongnya tidak merata antar
   operator.** Menara yang tidak terdaftar membuat daerah di sekitarnya terlihat
   lebih buruk dari kenyataan. Langkah 0 menemukan ketimpangan yang tajam:
   Telkomsel memegang 76% data Samarinda, XLSmart cuma 5%. Karena itu peta wajib
   membedakan "sinyal lemah" dari "tidak terdata" — kalau tidak, operator yang
   datanya bolong akan terlihat buruk tanpa pernah diuji.
4. **Yang dipakai adalah perkiraan letak sel, bukan koordinat menara hasil
   survei.** Basis data terbuka mengumpulkan posisi dari pengukuran ponsel orang
   banyak lalu merata-ratakannya. Satu menara memancarkan beberapa sel, dan
   posisi hasil perkiraan bisa meleset puluhan sampai ratusan meter.
5. **Tinggi antena, daya pancar, dan frekuensi tiap pemancar tidak diketahui —
   diasumsikan.** Data terbuka tidak memuatnya, dan operator tidak
   menerbitkannya. Karena semua pemancar terpaksa dianggap sama tinggi dan sama
   kuat, perbedaan antar lokasi datang hampir seluruhnya dari jarak dan bentuk
   tanah.
6. **Angka kekuatan sinyalnya ditaksir terlalu kuat, sekitar 30–50 dB.**
   Perhitungannya belum memasukkan dua hal: arah antena — orang yang berdiri
   persis di bawah menara sebenarnya berada di daerah buta antena, sedangkan di
   sini antena dianggap menyebar rata — dan redaman gedung serta pepohonan yang
   di kota menambah 10–30 dB.

   Akibatnya **angka dBm yang ditampilkan tidak boleh dibaca sebagai nilai
   sebenarnya.** Yang tetap bisa dipercaya adalah perbandingannya: operator mana
   yang lebih baik di suatu titik, dan daerah mana yang lebih baik dari daerah
   lain. Keduanya digerakkan kepadatan menara dan bentuk tanah, yang datang dari
   data nyata.

   Ini akan diperbaiki saat rumusnya naik ke ITU-R P.1812, yang punya model
   redaman gedung bawaan.
7. **Lokasi dari browser lebih kasar daripada GPS HP**, apalagi di dalam
   ruangan.

Menyembunyikan batasan ini akan membuat proyeknya terlihat naif. Menuliskannya
justru menunjukkan yang mengerjakan paham apa yang ia kerjakan.

## 8. Arsitektur

Tiga bagian yang bisa dikerjakan, diuji, dan diperbaiki terpisah. Pemisahan ini
disengaja karena pekerjaannya dipecah ke banyak sesi.

### Dapur — perhitungan (Python, jalan di laptop)

Mengunduh data menara dan data ketinggian, menghitung perkiraan sinyal untuk
setiap kotak di seluruh kota untuk setiap operator, lalu memotong hasilnya jadi
ubin-ubin siap tampil.

Dijalankan sesekali saat data diperbarui — bukan saat orang membuka situs.

Python dipilih karena sudah dipakai di dua proyek sebelumnya. Tenaga
belajar lebih baik dihabiskan untuk fisika propagasinya, bukan untuk bahasa
baru.

### Etalase — halaman web

Peta 3D berbasis MapLibre GL JS. Hanya mengunduh potongan peta sesuai daerah
yang sedang dilihat pengguna. Itu sebabnya bisa lancar walau datanya jutaan
titik, dan itu sebabnya bisa gratis.

MapLibre dipakai untuk hal yang sudah dipecahkan orang lain ribuan kali:
pemuatan ubin, tingkat kerincian saat zoom, pengelolaan memori kartu grafis,
proyeksi koordinat. Yang tetap dibangun dari nol dan tetap berat: mesin
prediksi, dapur pemotong ubin, dan cara menempelkan warna prediksi tepat di
atas permukaan tanah.

### Kotak surat — Tahap 2 saja

Penerima dan penyimpan kiriman pengukuran. Rencana: Supabase (PostgreSQL
dengan kemampuan geospasial PostGIS, ada paket gratis).

Kosong sampai Tahap 1 selesai.

### Biaya

Gratis dulu, tapi dirancang supaya gampang dipindahkan ke server berbayar kalau
mentok. Konsekuensi yang diterima: Tahap 1 tidak boleh membutuhkan server yang
menghitung saat halaman dibuka.

## 9. Tumpukan teknologi

Daftar ini mengikat. Menambah pustaka baru boleh, tapi harus ada alasannya —
bukan karena penasaran.

### Dapur — perhitungan

| Apa | Pilihan | Kenapa |
|---|---|---|
| Bahasa | Python 3.12 | Sudah dikuasai dari proyek sebelumnya |
| Pengelola paket | `uv` | Sudah terpasang di laptop, jauh lebih cepat dari pip |
| Perhitungan array | NumPy | Jutaan sel harus dihitung sekaligus, bukan satu per satu dengan perulangan Python |
| Baca data ketinggian | rasterio | Pustaka baku untuk berkas peta raster (GeoTIFF) |
| Ubah koordinat | pyproj | Derajat bumi ↔ meter; menghitung jarak pakai derajat itu salah |
| Pengujian | pytest | Baku di Python |
| Pemeriksa gaya | ruff | Cepat, sekaligus pemformat |

Kalau NumPy ternyata terlalu lambat, cadangannya Numba. **Jangan dipakai
sebelum terbukti lambat** — mengoptimalkan sesuatu yang belum diukur cuma
menambah kerumitan.

### Etalase — halaman web

| Apa | Pilihan | Kenapa |
|---|---|---|
| Bahasa | TypeScript | Kesalahan struktur data ubin ketahuan saat menulis, bukan saat dibuka orang. Juga nilai tambah di CV |
| Alat bangun | Vite | Cepat, siap pakai untuk TypeScript |
| Peta | MapLibre GL JS | Gratis, terbuka, sudah punya bentang alam 3D dan pemuatan ubin |
| Kerangka tampilan | **tidak ada** | Isi layarnya cuma peta, pemilih operator, dan keterangan warna. React/Vue tidak sepadan untuk itu |
| Gaya | CSS polos + custom properties | Sama seperti Timbang. Tailwind tidak dibutuhkan untuk layar sesederhana ini |
| Pengujian | Vitest | Pasangan alami Vite |

### Format data

- **Ubin sinyal: PNG, dengan nilai kekuatan sinyal disandikan ke dalam
  RGB** — bukan warna jadi. Alasannya: skema warna bisa diganti tanpa
  menghitung ulang berjam-jam, dan perbandingan antar operator bisa dikerjakan
  langsung di browser.
- **Ubin ketinggian: dibuat sendiri dari data mentah**, bukan mengambil dari
  layanan berbayar. Ini yang menjaga syarat "nol kunci API berbayar".
- **Keduanya dibungkus PMTiles** — satu berkas besar yang bisa dibaca
  sepotong-sepotong langsung lewat permintaan HTTP biasa. Ini kuncinya kenapa
  peta jutaan titik bisa disajikan tanpa server dan tanpa biaya.

### Menaruh online

**Belum diputuskan, dan memang belum boleh.** Pilihannya bergantung pada
ukuran keluaran yang baru diketahui setelah dapur jalan.

Syarat yang harus dipenuhi calon tempat: gratis, dan sanggup melayani berkas
besar dengan permintaan sebagian (HTTP range request) — tanpa itu, PMTiles
tidak berguna. Kandidat: Cloudflare Pages/R2, Vercel, GitHub Pages.

### Tahap 2

Supabase — PostgreSQL dengan PostGIS, ada paket gratis. Tidak dipasang sampai
Tahap 1 selesai.

### Bahasa penulisan

| Bagian | Bahasa |
|---|---|
| Nama variabel, fungsi, berkas | Inggris |
| Komentar dan dokumen | Indonesia |
| Pesan commit | Indonesia |
| Tulisan yang dilihat pengguna | Indonesia |

Nama berbahasa Inggris dipilih karena kode ini akan dilihat pemberi kerja, dan
istilah geospasial serta radio memang berbahasa Inggris — menerjemahkan *path
loss* jadi *redaman lintasan* di nama fungsi justru menyulitkan.

## 10. Tampilan dan pengalaman pakai

### Arah visual

**Peta survei teknis.** Latar krem keabuan, garis kontur tipis, keterangan
berhuruf mono, angka ditampilkan apa adanya. Terbaca sebagai alat ukur, bukan
produk pemasaran — sejalan dengan sifat proyek yang terus terang soal
ketidakpastiannya.

**Satu tampilan saja**, bukan terang dan gelap sekaligus. Peta punya banyak
lapisan warna yang harus diseimbangkan; menggandakannya berarti menggandakan
pekerjaan itu, dan versi keduanya biasanya jadi versi setengah hati.

Aturan yang mengikat:

- Bentang alamnya dibuat **redup**. Warna sinyal harus jadi satu-satunya hal
  pekat di layar — kalau bukitnya ikut berwarna-warni, datanya tenggelam.
- Huruf: satu grotesque untuk antarmuka, satu mono untuk semua angka dan label
  peta. Angka wajib mono supaya digitnya sejajar dan bisa dibandingkan sekilas.
- Huruf **disimpan sendiri**, bukan dipanggil dari layanan luar. Menjaga
  halaman tetap utuh tanpa sambungan ke pihak ketiga.

### Skema warna kekuatan sinyal

Ini keputusan teknis, bukan selera. Aturannya mengikat:

1. **Dilarang memakai merah–hijau.** Sekitar 8% laki-laki tidak bisa
   membedakannya — dan justru itu skema yang paling sering dipakai orang untuk
   "bagus/jelek". Peta ini akan dibaca laki-laki yang mau pindah kos.
2. **Terangnya harus naik atau turun berurutan**, bukan sekadar warnanya yang
   berganti. Ujinya sederhana: kalau dicetak hitam-putih, urutannya masih
   terbaca.
3. **Warna dibagi jadi beberapa tingkat (sekitar 5–7), bukan gradasi mulus.**
   Orang tidak bisa membaca gradasi mulus jadi angka, dan tingkatan lebih jujur
   terhadap ketelitian prediksi yang memang tidak setinggi itu.
4. **Skema yang sama dipakai untuk semua operator.** Kalau tiap operator punya
   skema sendiri, perbandingan jadi mustahil. Warna khas operator — kalau ada —
   hanya boleh muncul di tombol pemilihnya, tidak pernah di permukaan peta.
5. **Warna tidak boleh jadi satu-satunya pembawa informasi.** Menekan titik
   mana pun harus memunculkan angkanya.

### Tata letak

- Peta memenuhi layar. Panel kendali kecil dan bisa disembunyikan.
- Pemilih operator berupa **tombol sungguhan yang berjajar**, bukan menu
  gulung. Perbandingan harus satu ketukan — itu inti kegunaannya.
- **Keterangan warna selalu terlihat.** Tanpa itu peta ini tidak berarti apa-apa.
- Nama kecamatan dan kelurahan wajib tampil, supaya orang bisa menemukan
  daerahnya. Pencarian alamat ditunda, bukan untuk versi pertama.

### Di ponsel

**Wajib jalan di ponsel.** Orang akan membuka tautan ini dari HP, bukan laptop —
termasuk saat sedang melihat-lihat kos. Konsekuensinya: panel kendali berubah
jadi lembar yang muncul dari bawah, dan kerincian 3D diturunkan otomatis kalau
perangkatnya tidak kuat. Pengujian beban dilakukan di ponsel kelas menengah,
bukan hanya di laptop.

### Aksesibilitas

- Kontras teks memenuhi WCAG 2.2 tingkat AA.
- Semua kendali bisa dijangkau papan ketik, dengan penanda fokus yang terlihat.
- Gerak dimatikan saat perangkat meminta `prefers-reduced-motion`.
- Peta 3D pada dasarnya sulit dibaca pembaca layar. Karena itu wajib ada
  **cara lain membaca data yang sama** — daftar atau tabel per kecamatan.
  Ini bukan tambahan sopan santun: tanpa itu, sebagian orang tidak bisa
  memakai aplikasinya sama sekali.

### Nada bahasa

Bahasa Indonesia, terdengar seperti catatan orang yang mengukur sendiri.
Ketidakpastian dinyatakan terus terang, tidak dibungkus. Bukan nada korporat,
bukan nada pemasaran.

### Yang dilarang

- Slate kebiruan dengan aksen indigo atau ungu, gradasi, glassmorphism, sudut
  membulat besar. Ini kombinasi bawaan generator dan langsung terbaca begitu.
- Emoji, di mana pun.
- Istilah bergaya korporat: *Command Center*, *Dashboard*, *Insights*.
- Angka contoh atau data palsu yang tampak seperti data asli.
- Animasi yang memperlambat orang memahami peta.

### Alat bantu yang dipakai

Skill yang sudah terpasang dan relevan saat menggarap bagian ini: `hallmark`
(gerbang anti-tampilan-generik), `dataviz` (skema warna dan keterangan),
`accessibility` serta `frontend-a11y`, dan `humanizer` untuk teksnya.

## 11. Aturan kode

Aturan ini tidak boleh dilanggar tanpa membahasnya lebih dulu.

1. **Setiap rumus fisika wajib punya tes dengan angka acuan** dari sumber yang
   sudah diketahui hasilnya. Tanpa ini, peta yang salah tetap tampak indah dan
   tidak ada yang menyadarinya.
2. **Tidak ada angka ajaib.** Setiap konstanta diberi nama dan dicantumkan
   sumbernya di komentar.
3. **Perhitungan matematika harus fungsi murni** — masukan sama selalu
   menghasilkan keluaran sama, tidak menyentuh berkas atau jaringan. Hanya
   dengan begitu bisa diuji.
4. **Dapur harus bisa dilanjutkan, bukan diulang dari nol**, kalau berhenti di
   tengah jalan.
5. **Data mentah tidak masuk git.** Yang masuk git adalah skrip pengunduhnya.
6. **Batasan dan ketidakpastian ditampilkan di peta**, tidak disembunyikan.
7. **Nol kunci API berbayar di dalam kode.** Kalau sebuah layanan memerlukan
   kunci berbayar, itu tanda layanannya salah pilih.
8. **Pesan commit berbahasa Indonesia**, tanpa jejak alat bantu AI.

### Susunan folder

```
dapur/        Python: unduh data, hitung propagasi, potong jadi ubin
etalase/      halaman web: peta 3D
kotak-surat/  Tahap 2 saja, kosong dulu
data/         data mentah & hasil hitung — tidak masuk git
docs/         PRD dan catatan keputusan
```

## 12. Risiko

| Risiko | Akibat | Penanganan |
|---|---|---|
| Data menara Samarinda bolong parah | Proyek tidak bisa jalan sebagaimana dirancang | Langkah 0 sebagai gerbang, sebelum ada kode terbuang |
| Perhitungan seluruh kota terlalu lama di laptop | Iterasi jadi lambat dan menyiksa | Mulai dari kotak kasar, perhalus bertahap; dapur bisa dilanjutkan |
| Ukuran berkas ubin melebihi batas hosting gratis | Tidak bisa diunggah | Batasi tingkat zoom dan kerincian; ukur ukurannya sejak awal, bukan di akhir |
| Prediksi meleset jauh dari kenyataan | Kepercayaan pengunjung turun | Diterima sebagai sifat proyek; ditulis terang di peta, dan justru itu alasan Tahap 2 ada |
| Proyek terlalu besar lalu ditinggalkan | Tidak ada yang bisa dipamerkan | Tahap 1 dirancang berdiri sendiri — kalau berhenti di situ pun sudah utuh |

## 13. Ukuran keberhasilan

**Tahap 1 dianggap berhasil kalau:**

- Orang yang belum pernah melihatnya bisa menjawab "operator mana yang bagus di
  daerah saya" dalam waktu di bawah satu menit, tanpa dijelaskan.
- Peta terbuka dan bisa diputar dengan lancar di laptop biasa.
- Seluruh Kota Samarinda tercakup, bukan sebagian.

**Keberhasilan sebagai portofolio:** ada bagian yang membuat orang bertanya
"ini kamu hitung sendiri?" — dan jawabannya iya, dengan tes yang membuktikan
hitungannya benar.

## 14. Keputusan yang sudah dikunci

Berikut keputusan yang sudah diambil beserta alasannya. Kalau sesi berikutnya
ingin mengubah salah satunya, ubah dokumen ini sekalian — jangan diam-diam
menyimpang.

| Keputusan | Alasan |
|---|---|
| Web browser, bukan aplikasi HP | Tinggal kirim link; tidak ada penghalang mencoba |
| Prediksi dulu, koreksi menyusul | Menyelesaikan masalah peta kosong di hari pertama |
| Dibedakan per operator — **tiga**, bukan lima | Itu pertanyaan yang orang benar-benar punya. Setelah Indosat–Tri bergabung (2022) dan XL–Smartfren–Smart Telecom jadi XLSmart (April 2025), yang tersisa: Telkomsel, Indosat Ooredoo Hutchison, XLSmart. Kode MNC lama dikelompokkan ke ketiganya |
| Seluruh Kota Samarinda | Membuat tantangan skala jadi nyata, bukan mainan |
| Bentang alam 3D, bukan gedung | Ketinggian tanah adalah penyebab sinyal terhalang, jadi 3D-nya menjelaskan sebab, bukan hiasan |
| Gedung 3D dan seluruh jalan ditampilkan — **diubah 15 Agustus 2026** | Ali meminta peta kota, bukan peta data: "saya mau seperti kota". Nama kecamatan terlalu kasar untuk menemukan tempat sendiri. Baris di atas dibatalkan **sebagian**: gedung sekarang ditegakkan 3D, tapi tetap **tidak ikut perhitungan propagasi** — yang menghalangi sinyal tetap ketinggian tanah |
| Tinggi gedung diasumsikan, dan dinyatakan di halaman | Dari 241.738 gedung Samarinda di OSM, cuma **57** punya tinggi sebenarnya dan 2.413 punya jumlah lantai. Sisanya ditegakkan 2 lantai × 3,5 m. Ini melanggar semangat "dilarang data palsu yang tampak asli" di bagian 10, **kecuali** kalau dinyatakan — maka halaman wajib menyebutnya, sama seperti asumsi tinggi antena |
| MapLibre, bukan Three.js dari nol | Kesulitan dipindah ke bagian yang tidak bisa disalin orang lain |
| Python untuk dapur | Sudah dikuasai; hemat tenaga belajar untuk fisikanya |
| Gratis dulu, siap dipindah | Menghindari tagihan berjalan untuk proyek yang belum tentu diteruskan |
| TypeScript untuk web | Kesalahan struktur data ketahuan lebih awal; nilai tambah di CV |
| Tanpa kerangka tampilan | Layarnya terlalu sederhana untuk membenarkan React/Vue |
| PMTiles untuk ubin | Satu berkas, tanpa server, bisa dibaca sebagian — inilah yang membuat gratis jadi mungkin |
| Nilai sinyal disandikan ke RGB, bukan warna jadi | Skema warna bisa diganti tanpa menghitung ulang berjam-jam |
| Nama kode berbahasa Inggris | Dilihat pemberi kerja; istilah radio & geospasial memang Inggris |
| Tampilan peta survei teknis, satu suasana saja | Terbaca sebagai alat ukur, bukan produk pemasaran; menggandakan terang/gelap menggandakan pekerjaan penyeimbangan warna |
| Skema warna bertingkat, bukan merah–hijau | Merah–hijau tidak terbaca oleh ~8% laki-laki — pembaca utama peta ini |
| Wajib jalan di ponsel | Orang membuka tautan ini dari HP, termasuk saat sedang melihat kos |
| Wajib ada cara lain membaca data selain peta | Peta 3D tidak terbaca pembaca layar; tanpa itu sebagian orang tidak bisa memakainya sama sekali |

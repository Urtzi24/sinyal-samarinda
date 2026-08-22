# Spesifikasi Fitur: Peta Prediksi Sinyal Samarinda (Tahap 1)

**Feature Branch**: `master` — tidak ada cabang khusus untuk tahap ini

**Created**: 2026-08-14

**Status**: Draft

**Input**: Tuangkan `docs/PRD.md` jadi spesifikasi untuk Tahap 1 (mesin
prediksi + peta 3D). Jangan mengulang brainstorming — keputusan terkunci ada di
PRD bagian 14.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Membandingkan operator di satu daerah (Priority: P1)

Seseorang berencana pindah kos ke suatu daerah di Samarinda. Ia membuka tautan,
menemukan daerah itu di peta, lalu menekan tombol tiap operator bergantian dan
melihat warna di daerah tersebut berubah. Ia menekan titik tepat di lokasi kos
incarannya dan mendapat angka perkiraan untuk operator yang sedang dipilih. Dari
situ ia menyimpulkan sendiri operator mana yang paling masuk akal, tanpa ada yang
menyarankan merek apa pun kepadanya.

**Why this priority**: Inilah pertanyaan yang membuat produk ini ada. Kalau cuma
cerita ini yang jadi, produknya sudah berguna dan sudah bisa dipamerkan.

**Independent Test**: Beri tautan ke orang yang belum pernah melihatnya, sebutkan
satu nama daerah, dan minta ia menyebut operator terbaik di sana. Berhasil kalau
ia sampai pada jawaban tanpa dijelaskan lebih dulu.

**Acceptance Scenarios**:

1. **Given** halaman terbuka pertama kali, **When** pengguna belum melakukan apa
   pun, **Then** peta sudah menampilkan satu operator terpilih beserta warnanya,
   dan keterangan warnanya terlihat — bukan peta kosong.
2. **Given** peta sedang menampilkan operator A, **When** pengguna menekan tombol
   operator B, **Then** warna di seluruh peta berganti ke perkiraan operator B
   dalam satu ketukan, tanpa memuat ulang halaman dan tanpa berpindah tampilan.
3. **Given** peta menampilkan suatu operator, **When** pengguna menekan satu titik
   di peta, **Then** muncul angka perkiraan untuk titik dan operator itu, dengan
   penanda yang jelas bahwa angka tersebut prediksi.
4. **Given** pengguna berada di daerah yang datanya tidak memadai, **When** ia
   menekan titik di sana, **Then** yang muncul adalah keterangan "data tidak
   memadai", bukan angka yang tampak sahih.
5. **Given** halaman baru dibuka, **When** pengguna ingin memakainya, **Then**
   tidak ada permintaan mendaftar, masuk akun, atau memberi izin apa pun sebelum
   peta bisa dipakai.

---

### User Story 2 - Melihat sebab, bukan cuma hasil (Priority: P2)

Pengguna melihat daerahnya berwarna buruk dan ingin tahu kenapa. Ia memiringkan
dan memutar peta, lalu melihat bentuk permukaan tanah sebenarnya — dan tampak
bahwa ada punggungan bukit antara daerahnya dan sumber sinyal terdekat.

**Why this priority**: Membedakan produk ini dari peta cakupan mana pun yang sudah
ada, dan menjadi bukti bahwa perkiraannya berasal dari perhitungan, bukan tebakan.
Tetap di bawah P1 karena tanpa cerita ini pun pertanyaan utama sudah terjawab.

**Independent Test**: Pilih satu daerah yang diketahui terhalang bukit, miringkan
peta, dan pastikan penghalangnya terlihat secara visual tanpa penjelasan tambahan.

**Acceptance Scenarios**:

1. **Given** peta terbuka, **When** pengguna memutar, memiringkan, dan memperbesar,
   **Then** permukaan bergerak mengikuti tanpa tersendat, dan ketinggiannya sesuai
   bentuk tanah sebenarnya.
2. **Given** peta dimiringkan, **When** pengguna melihat daerah berbukit, **Then**
   warna perkiraan sinyal tetap menempel mengikuti permukaan tanah, tidak melayang
   atau tembus di bawahnya.
3. **Given** perangkat pengguna tidak sanggup menampilkan kerincian penuh, **When**
   halaman dibuka, **Then** kerincian diturunkan otomatis dan peta tetap bisa
   dipakai, bukan gagal terbuka.

---

### User Story 3 - Membaca data yang sama tanpa peta (Priority: P3)

Pengguna yang memakai pembaca layar — atau siapa pun yang perangkatnya tidak
sanggup menampilkan peta — membuka daftar per kecamatan dan membaca perkiraan tiap
operator dalam bentuk tabel.

**Why this priority**: Prioritas di sini menyatakan **urutan pengerjaan**, bukan
boleh atau tidaknya dilewatkan. Konstitusi mewajibkannya sebelum rilis: peta 3D
pada dasarnya tidak terbaca pembaca layar, jadi tanpa jalur ini sebagian orang
tidak bisa memakai produknya sama sekali.

**Independent Test**: Matikan tampilan peta sepenuhnya dan telusuri halaman hanya
dengan papan ketik dan pembaca layar. Berhasil kalau perkiraan tiap operator per
kecamatan tetap bisa dibaca dan dibandingkan.

**Acceptance Scenarios**:

1. **Given** pengguna memakai pembaca layar, **When** ia menelusuri halaman,
   **Then** ia menemukan daftar kecamatan beserta perkiraan tiap operator tanpa
   perlu berinteraksi dengan peta.
2. **Given** pengguna hanya memakai papan ketik, **When** ia berpindah antar
   kendali, **Then** setiap kendali bisa dijangkau dan posisi fokusnya terlihat.
3. **Given** perangkat meminta pengurangan gerak, **When** halaman dibuka,
   **Then** animasi dan perpindahan bergerak dimatikan.

---

### Edge Cases

- Pengguna menekan titik di luar batas Kota Samarinda — sistem menyatakan titik itu
  di luar cakupan, bukan memberi angka hasil terkaan.
- Suatu wilayah tidak punya menara terdaftar di sekitarnya — wilayah itu ditandai
  sebagai "data tidak memadai" dan **dibedakan secara visual** dari wilayah yang
  memang sinyalnya lemah. Dua hal ini tidak boleh terlihat sama.
- Satu operator punya data jauh lebih sedikit dari operator lain — perbedaan
  kelengkapan itu harus terbaca, supaya operator dengan data bolong tidak terlihat
  buruk padahal cuma tidak terdata.
- Pengguna memperbesar melebihi kerincian perhitungan — sistem tidak boleh
  menampilkan kehalusan yang tidak dimilikinya.
- Layar sangat sempit — panel kendali berubah jadi lembar yang muncul dari bawah,
  dan keterangan warna tetap terlihat.
- Sambungan internet lambat — peta memuat bertahap per daerah yang sedang dilihat;
  bagian yang belum termuat ditandai jelas, bukan dibiarkan kosong tanpa keterangan.
- Pengguna memutar perangkat atau mengubah ukuran jendela — tata letak menyesuaikan
  tanpa kehilangan posisi peta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistem MUST menampilkan seluruh wilayah administratif Kota Samarinda.
  Tidak boleh ada bagian di dalam batas kota yang tidak tercakup.
- **FR-002**: Sistem MUST menampilkan permukaan tiga dimensi yang tingginya
  mengikuti ketinggian tanah sebenarnya, dan MUST bisa diputar, dimiringkan, serta
  diperbesar-diperkecil.
- **FR-003**: Pengguna MUST bisa memilih operator lewat tombol berjajar yang
  semuanya terlihat sekaligus. Menu gulung DILARANG — perbandingan harus satu
  ketukan.
- **FR-004**: Warna perkiraan di peta MUST berganti seketika saat operator diganti,
  tanpa memuat ulang halaman dan tanpa mengubah posisi maupun sudut pandang peta.
- **FR-005**: Menekan titik mana pun di dalam cakupan MUST menampilkan nilai
  perkiraan di titik itu untuk operator yang sedang dipilih. Warna DILARANG jadi
  satu-satunya pembawa informasi.
- **FR-006**: Setiap nilai yang ditampilkan MUST terbaca sebagai prediksi, bukan
  sebagai hasil pengukuran.
- **FR-007**: Skema warna MUST dibagi 5–7 tingkat, dengan terang yang naik atau
  turun berurutan sehingga urutannya tetap terbaca bila dicetak hitam-putih.
  Skema merah–hijau DILARANG.
- **FR-008**: Skema warna yang sama MUST dipakai untuk semua operator. Warna khas
  operator hanya boleh muncul di tombol pemilihnya, tidak pernah di permukaan peta.
- **FR-009**: Keterangan warna MUST selalu terlihat selama peta ditampilkan.
- **FR-010**: Nama kecamatan dan kelurahan MUST tampil di peta, supaya pengguna
  bisa menemukan daerahnya tanpa fitur pencarian.
- **FR-011**: Sistem MUST membedakan secara visual antara "perkiraan sinyal lemah"
  dan "data tidak memadai".
- **FR-012**: Keempat batasan kejujuran — perkiraan bukan pengukuran, data menara
  terbuka tidak lengkap, rumus tidak tahu kondisi terkini, dan lokasi dari peramban
  lebih kasar daripada GPS — MUST terbaca di halaman peta itu sendiri.
- **FR-013**: Sistem MUST menyediakan cara membaca perkiraan yang sama tanpa
  memakai peta, dalam bentuk daftar atau tabel per kecamatan.
- **FR-014**: Semua kendali MUST bisa dijangkau dan dioperasikan dengan papan
  ketik, dengan penanda fokus yang terlihat.
- **FR-015**: Kontras teks MUST memenuhi WCAG 2.2 tingkat AA.
- **FR-016**: Gerak MUST dimatikan saat perangkat meminta pengurangan gerak.
- **FR-017**: Sistem MUST bisa dipakai penuh di ponsel. Pada layar sempit, panel
  kendali MUST berubah menjadi lembar yang muncul dari bawah.
- **FR-018**: Sistem MUST menurunkan kerincian tampilan secara otomatis pada
  perangkat yang tidak sanggup, alih-alih gagal terbuka.
- **FR-019**: Sistem MUST bisa dipakai tanpa mendaftar, masuk akun, atau memberi
  izin apa pun.
- **FR-020**: Perkiraan MUST sudah tersedia saat halaman dibuka. Pengguna DILARANG
  diminta menunggu perhitungan berjalan.
- **FR-021**: Sistem DILARANG merekomendasikan merek atau produk operator tertentu.
  Yang disajikan hanya data; kesimpulan diserahkan ke pengguna.
- **FR-022**: Saat pengguna menekan sebuah titik, sistem MUST menampilkan dua hal
  berdampingan: tingkat perkiraan pada skala yang sama dengan tingkatan warna, dan
  nilai teknis kekuatan sinyalnya. Tingkat melayani pembaca awam; nilai teknis
  melayani pembaca yang ingin memeriksa hasil hitungan. Keduanya MUST disertai
  penanda bahwa angka itu prediksi.
- **FR-023**: Perbandingan antar-operator MUST dilakukan dengan cara mengganti
  operator satu per satu. Sistem DILARANG menampilkan lapisan "operator terkuat di
  sini" maupun dua operator berdampingan dalam satu layar. Menunjuk pemenang
  terbaca sebagai mengarahkan pengguna ke satu merek — dan itu sudah ditolak di
  PRD bagian 3.
- **FR-024**: Halaman MUST menyatakan bahwa tinggi antena, daya pancar, dan
  frekuensi tiap pemancar **diasumsikan, bukan diketahui**. Pernyataan ini MUST
  tampil bersama batasan lain di FR-012, bukan dipisah ke halaman lain.
- **FR-025**: Halaman MUST menyatakan bahwa **angka kekuatan sinyalnya ditaksir
  terlalu kuat**, dan bahwa yang bisa dipercaya adalah perbandingan antar
  operator serta antar lokasi — bukan nilai dBm-nya sendiri. Pernyataan ini MUST
  terbaca di dekat tempat angka itu muncul, bukan cuma di bagian batasan.

### Key Entities

- **Titik perkiraan**: satu satuan wilayah kecil di dalam Kota Samarinda. Punya
  posisi, nilai perkiraan per operator, dan penanda apakah datanya memadai.
- **Operator**: penyelenggara jaringan seluler yang bisa dipilih pengguna. Punya
  nama dan warna tombol; tidak punya skema warna peta sendiri.
- **Menara pemancar**: sumber sinyal. Punya posisi, operator pemilik, dan
  ketinggian. Menjadi masukan perhitungan, bukan sesuatu yang wajib ditampilkan
  ke pengguna.
- **Permukaan ketinggian**: bentuk tanah Kota Samarinda. Menjadi masukan
  perhitungan sekaligus yang ditampilkan sebagai bentang alam 3D.
- **Wilayah administratif**: kecamatan dan kelurahan. Dipakai sebagai penanda lokasi
  di peta dan sebagai pengelompokan pada jalur baca alternatif.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Orang yang belum pernah melihatnya bisa menjawab "operator mana yang
  sinyalnya bagus di daerah saya" dalam waktu di bawah satu menit, tanpa dijelaskan
  lebih dulu.
- **SC-002**: 100% wilayah di dalam batas Kota Samarinda tercakup — nol daerah
  kosong tanpa keterangan.
- **SC-003**: Berganti dari satu operator ke operator lain dan melihat perbedaannya
  butuh tepat satu ketukan.
- **SC-004**: Peta bisa diputar, dimiringkan, dan diperbesar tanpa tersendat, baik
  di laptop biasa maupun di ponsel kelas menengah.
- **SC-005**: 100% angka yang ditampilkan disertai penanda bahwa itu prediksi.
- **SC-006**: Seluruh perkiraan yang bisa dibaca lewat peta juga bisa dibaca lewat
  jalur tanpa peta, dan bisa diselesaikan hanya dengan papan ketik dan pembaca layar.
- **SC-007**: 100% teks memenuhi kontras WCAG 2.2 tingkat AA.
- **SC-008**: Batasan kejujuran terbaca tanpa harus dicari — terlihat di layar
  pertama atau paling jauh satu ketukan dari sana.
- **SC-009**: Peta bisa dipakai tanpa satu pun permintaan mendaftar, masuk akun,
  atau izin perangkat.
- **SC-010**: Wilayah "data tidak memadai" bisa dibedakan dari wilayah "sinyal
  lemah" oleh orang yang belum pernah melihat peta ini, tanpa membaca keterangan
  tambahan.

## Assumptions

- **Langkah 0 sudah lolos** (14 Agustus 2026). Asumsi dasarnya — data posisi
  pemancar tersedia terbuka, bisa dipisahkan per operator, dan data ketinggian
  tanah tersedia dengan kerincian memadai — sudah diuji dengan data sungguhan,
  bukan diandaikan. Angkanya di `docs/LANGKAH-0.md`.
- **Operatornya tiga, bukan lima:** Telkomsel, Indosat Ooredoo Hutchison, dan
  XLSmart. Dua penggabungan sudah terjadi sejak data terbuka itu dikumpulkan. Ini
  yang menentukan jumlah tombol di pemilih operator.
- **Kelengkapan data timpang antar operator** — Telkomsel 76%, XLSmart 5% pada
  data yang diperiksa. FR-011 bukan lagi pengaman teoretis; tanpa itu XLSmart akan
  terlihat buruk di seluruh kota padahal cuma tidak terdata.
- **Tinggi antena, daya pancar, dan frekuensi diasumsikan.** Tidak ada di data
  terbuka mana pun dan tidak diterbitkan operator. Konsekuensinya semua pemancar
  dianggap sama, sehingga perbedaan antar lokasi datang hampir seluruhnya dari
  jarak dan bentuk tanah. Ini diterima sebagai sifat proyek, dan wajib dinyatakan
  di halaman lewat FR-024.
- **Data menara terbuka tidak akan pernah lengkap.** Diterima sebagai sifat
  proyek, bukan cacat yang harus ditutup. Konsekuensinya ditangani lewat FR-011
  dan FR-012.
- **Perkiraan akan meleset di sebagian tempat.** Rumus propagasi tidak tahu ada
  gedung baru, menara mati, atau jaringan sedang padat. Diterima dan dinyatakan
  terbuka di halaman.
- **Tahap 2 di luar lingkup.** Pengukuran oleh pengunjung dan koreksi otomatis
  tidak termasuk spesifikasi ini, dan tidak boleh dikerjakan sebelum Tahap 1
  memenuhi definisi selesai.
- **Pencarian alamat di luar lingkup.** Pengguna menemukan daerahnya lewat nama
  kecamatan dan kelurahan di peta.
- **Mode perbandingan langsung di luar lingkup.** Lapisan "operator terkuat" dan
  tampilan dua operator berdampingan ditolak untuk Tahap 1 — bukan karena berat,
  tapi karena menunjuk pemenang berarti mengarahkan orang ke satu merek. Peta
  menyajikan data; kesimpulan tetap milik pengguna.
- **Satu kota saja.** Kota selain Samarinda ditolak dengan sengaja.
- **Pengguna punya sambungan internet yang cukup** untuk memuat peta secara
  bertahap. Pemakaian sepenuhnya luring tidak termasuk lingkup.
- **Kerincian perhitungan berkembang bertahap** — mulai kasar untuk membuktikan
  seluruh alurnya jalan, lalu diperhalus. Kerincian akhir belum ditetapkan di
  spesifikasi ini karena bergantung pada hasil pengukuran waktu hitung dan ukuran
  keluaran.

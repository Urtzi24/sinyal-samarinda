# Daftar Periksa Mutu Spesifikasi: Peta Prediksi Sinyal Samarinda (Tahap 1)

**Tujuan**: memeriksa kelengkapan dan mutu spesifikasi sebelum masuk tahap
perencanaan
**Dibuat**: 2026-08-14
**Fitur**: [spec.md](../spec.md)

## Mutu Isi

- [x] Tidak ada rincian implementasi (bahasa, kerangka kerja, API)
- [x] Berfokus pada nilai bagi pengguna, bukan cara membangunnya
- [x] Bisa dibaca orang non-teknis
- [x] Semua bagian wajib terisi

## Kelengkapan Kebutuhan

- [x] Tidak ada penanda [NEEDS CLARIFICATION] tersisa
- [x] Kebutuhan bisa diuji dan tidak bermakna ganda
- [x] Ukuran keberhasilan bisa diukur
- [x] Ukuran keberhasilan bebas dari rincian teknologi
- [x] Semua skenario penerimaan sudah ditulis
- [x] Kasus tepi sudah diidentifikasi
- [x] Lingkup dibatasi dengan jelas (Tahap 2, pencarian alamat, mode perbandingan
      langsung, dan kota lain dinyatakan di luar lingkup)
- [x] Ketergantungan dan asumsi sudah diidentifikasi (gerbang Langkah 0 tercatat
      sebagai asumsi utama)

## Kesiapan Fitur

- [x] Semua kebutuhan fungsional punya kriteria penerimaan yang jelas
- [x] Skenario pengguna mencakup alur utama
- [x] Fitur memenuhi hasil terukur yang ditetapkan di Ukuran Keberhasilan
- [x] Tidak ada rincian implementasi yang bocor ke spesifikasi

## Catatan

Semua butir lolos. Spesifikasi siap masuk tahap perencanaan.

Dua pertanyaan yang sempat tertahan sudah dijawab Ali pada 2026-08-14, dan
jawabannya masuk ke spesifikasi:

- **FR-022 — bentuk angka saat titik ditekan.** Tingkat dan nilai teknis
  ditampilkan berdampingan. Tingkat melayani orang yang mau pindah kos; nilai
  teknis melayani orang yang ingin memeriksa hasil hitungan.
- **FR-023 — lingkup perbandingan.** Ditolak untuk Tahap 1. Alasan Ali: menunjuk
  operator terkuat terbaca seperti mengarahkan orang ke satu merek. Ini menguatkan
  penolakan yang sudah ada di PRD bagian 3, jadi dicatat sebagai batas lingkup,
  bukan sekadar penundaan.

Kedua jawaban tidak bertentangan dengan tabel keputusan terkunci di PRD bagian 14,
jadi PRD tidak perlu diubah.

**Tambahan setelah perencanaan (14 Agustus 2026):** pemeriksaan konstitusi
pasca-desain menemukan bahwa tinggi antena, daya pancar, dan frekuensi pemancar
tidak ada di data mana pun dan harus diasumsikan — sumber ketidakpastian yang
kemungkinan terbesar, tapi belum diwajibkan tampil di halaman. Prinsip VI
karenanya belum terpenuhi. Ditutup dengan **FR-024** dan poin baru di PRD bagian 7.
Jumlah kebutuhan fungsional jadi 24.

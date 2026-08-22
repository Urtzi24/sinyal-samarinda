# Maps Samarinda

Peta 3D Kota Samarinda — bentang alam, gedung, dan jalan — yang menampilkan
perkiraan kualitas sinyal tiap operator seluler di setiap titik kota.

Perkiraannya dihitung dari posisi pemancar seluler dan bentuk permukaan tanah
dengan rumus propagasi radio — termasuk memperhitungkan bukit yang menghalangi
sinyal.

**Status:** dapur jalan penuh (unduh → hitung → ubin), petanya tampil. Angka dBm
mutlaknya masih ditaksir terlalu kuat; yang bisa dipercaya perbandingannya.

Baca [docs/MULAI-DARI-SINI.md](docs/MULAI-DARI-SINI.md) kalau mau mengerjakannya,
atau [docs/PRD.md](docs/PRD.md) kalau mau tahu apa yang dibangun dan kenapa.

## Susunan

```
dapur/        Python: unduh data, hitung propagasi, potong jadi ubin
etalase/      halaman web: peta 3D
kotak-surat/  Tahap 2 saja, kosong dulu
data/         data mentah & hasil hitung — tidak masuk git
docs/         PRD, konstitusi rujukan, hasil Langkah 0
specs/        spesifikasi, rencana, dan daftar tugas
tests/        tes dapur
```

## Menjalankan

**Dapur** perlu `uv`. Di laptop ini `uv` terpasang lewat pip dan **tidak ada di
PATH**, jadi perintahnya lewat `python -m uv`:

```bash
python -m uv sync
python -m uv run pytest
python -m uv run ruff check .
```

**Etalase:**

```bash
cd etalase
npm install
npm run dev
```

## Batasan

Peta ini menampilkan **prediksi**, bukan hasil pengukuran. Rumusnya tidak tahu
ada gedung baru, menara yang sedang mati, atau jaringan yang sedang padat.

Tiga hal yang perlu diketahui sejak awal:

- **Data pemancar terbuka tidak pernah lengkap, dan bolongnya tidak merata antar
  operator.** Pemeriksaan Langkah 0 menemukan satu operator memegang 76% data,
  yang lain cuma 5%.
- **Yang dipakai adalah perkiraan letak sel**, bukan koordinat menara hasil
  survei — bisa meleset puluhan sampai ratusan meter.
- **Tinggi antena, daya pancar, dan frekuensi tidak diketahui dan diasumsikan.**
  Ini kemungkinan sumber kesalahan terbesar, lebih besar daripada rumusnya
  sendiri.

Rincian lengkapnya di bagian 7 PRD, dan hasil pemeriksaan datanya di
[docs/LANGKAH-0.md](docs/LANGKAH-0.md).

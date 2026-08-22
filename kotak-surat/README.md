# Kotak surat

Kosong, dan itu disengaja.

Bagian ini baru diisi di **Tahap 2**, saat pengunjung bisa menekan "ukur di sini"
dan hasilnya dipakai mengoreksi perkiraan di wilayah itu. PRD bagian 6 melarang
mengerjakannya sebelum Tahap 1 memenuhi definisi selesai — dan konstitusi
menjadikan larangan itu mengikat.

Rencana isinya: penerima dan penyimpan kiriman pengukuran, di atas PostgreSQL
dengan PostGIS.

Yang sudah harus dipikirkan sejak hari pertama Tahap 2: kiriman tanpa akun bisa
disalahgunakan. Perlu pembatasan laju dan penolakan data yang menyimpang jauh.

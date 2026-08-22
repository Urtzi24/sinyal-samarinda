"""Konstanta dapur.

Tiap angka di berkas ini punya sumber tertulis. Itu bukan kesopanan — Prinsip II
konstitusi melarang angka ajaib, dan konstanta radio tanpa asal-usul tidak bisa
diperiksa ulang, tidak bisa diperbaiki, dan tidak bisa dipertanggungjawabkan saat
ada yang bertanya.

Konstanta asumsi pemancar ada di bagian terakhir, dengan peringatannya sendiri:
angka-angka itu **diasumsikan**, bukan diketahui, dan itu sumber ketidakpastian
terbesar di seluruh peta.
"""

from typing import Final, NamedTuple


class BoundingBox(NamedTuple):
    """Kotak batas dalam derajat WGS84."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float


class TransmitterAssumptions(NamedTuple):
    """Ciri pemancar yang diasumsikan untuk satu jenis jaringan.

    Tidak satu pun dari angka ini ada di data terbuka. Semuanya nilai wakil dari
    ITU-R M.2292-0 untuk sel makro perkotaan — lihat catatan di bawah.
    """

    frequency_mhz: float
    antenna_height_m: float
    eirp_dbm: float


# ---------------------------------------------------------------------------
# Tetapan fisika
# ---------------------------------------------------------------------------

# Laju cahaya di ruang hampa, meter per detik.
#
# Nilainya eksak menurut definisi — sejak 1983 satu meter justru DIDEFINISIKAN
# lewat angka ini, jadi ia tidak punya ketidakpastian pengukuran.
#
# Sumber: Sistem Satuan Internasional (SI), definisi meter.
SPEED_OF_LIGHT_M_S: Final = 299_792_458.0

# Panjang satu derajat lintang di permukaan bumi, meter. Nilai rata-rata; yang
# sebenarnya bervariasi dari sekitar 110,6 km di khatulistiwa sampai 111,7 km di
# kutub.
#
# Ketelitian sekasar ini CUKUP karena angka ini hanya dipakai untuk melebarkan
# kotak penyaringan. Meleset beberapa ratus meter pada batas 20 km tidak
# mengubah satu pun hasil. Perhitungan jarak yang sebenarnya memakai pyproj,
# bukan angka ini — dan itu memang keharusan, karena menghitung jarak dari
# derajat secara langsung itu salah.
METERS_PER_DEGREE_LATITUDE: Final = 111_320.0

# ---------------------------------------------------------------------------
# Wilayah
# ---------------------------------------------------------------------------

# Relasi batas administratif Kota Samarinda di OpenStreetMap.
#
# Namanya di OSM cuma "Samarinda", BUKAN "Kota Samarinda". Kueri dengan nama yang
# salah mengembalikan nol tanpa pesan galat — dan nol itu terbaca persis seperti
# "tidak ada data". Jebakan ini sudah memakan satu kali di Langkah 0, jadi
# rujuklah relasi ini lewat nomornya, bukan lewat namanya.
#
# Sumber: OpenStreetMap, relasi 14921097, diambil 2026-08-14.
SAMARINDA_OSM_RELATION_ID: Final = 14921097

# Kotak batas Kota Samarinda. Kira-kira 27 km barat-timur x 45 km utara-selatan.
# Sumber: kotak batas relasi OSM di atas, diambil 2026-08-14.
SAMARINDA_BBOX: Final = BoundingBox(
    min_lon=117.0540,
    min_lat=-0.7168,
    max_lon=117.2982,
    max_lat=-0.3144,
)

# Penyaringan pemancar dilebihkan keluar dari batas kota: pemancar di luar batas
# administratif tetap menyinari kota, jadi memotong tepat di batas akan membuat
# pinggiran kota terlihat lebih buruk dari kenyataan.
#
# NILAI KERJA, belum tervalidasi. Angka ini dipilih karena melampaui jangkauan
# praktis sel makro pada pita yang dipakai di Indonesia, tapi belum diuji
# terhadap modelnya sendiri. Setelah rumus propagasi ada (T013), nilai ini wajib
# diperiksa ulang: batas yang benar adalah jarak saat sumbangan sebuah pemancar
# jatuh di bawah tingkat terlemah yang ditampilkan peta.
TRANSMITTER_SEARCH_BUFFER_M: Final = 20_000

# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------

# Kode negara seluler untuk Indonesia.
# Sumber: daftar Mobile Country Code ITU-T E.212.
INDONESIA_MCC: Final = 510

# Pemetaan kode jaringan (MNC) ke operator yang ada pada 2026.
#
# Data terbuka memuat lima kode, tapi hari ini operatornya tinggal tiga — dua
# penggabungan terjadi setelah data itu dikumpulkan:
#   - Indosat + Tri                      -> Indosat Ooredoo Hutchison (2022)
#   - XL + Smartfren + Smart Telecom     -> XLSmart (beroperasi 16 April 2025)
#
# Kode yang tidak ada di sini WAJIB dicatat dan dibuang, bukan diam-diam
# dianggap operator terdekat.
#
# Sumber: docs/LANGKAH-0.md, bagian "Operatornya sekarang tiga, bukan lima".
MNC_TO_OPERATOR: Final[dict[int, str]] = {
    10: "telkomsel",
    1: "ioh",
    89: "ioh",
    11: "xlsmart",
    28: "xlsmart",
}

# Nama yang dilihat pengguna. Bahasa Indonesia, sesuai PRD bagian 9.
OPERATOR_DISPLAY_NAMES: Final[dict[str, str]] = {
    "telkomsel": "Telkomsel",
    "ioh": "Indosat Ooredoo Hutchison",
    "xlsmart": "XLSmart",
}

# ---------------------------------------------------------------------------
# Sumber data — ketinggian tanah
# ---------------------------------------------------------------------------

# Ubin Copernicus DEM GLO-30 yang menutupi seluruh Kota Samarinda.
# Satu ubin sudah cukup; sudah diperiksa langsung di Langkah 0 — HTTP 200, tanpa
# akun, tanpa kunci, melayani permintaan sebagian, dan tanda tangan berkasnya
# memang Cloud-Optimized GeoTIFF yang sah. Ukurannya 23 MB.
#
# Sumber: docs/LANGKAH-0.md, syarat 3.
DEM_BASE_URL: Final = "https://copernicus-dem-30m.s3.amazonaws.com"
DEM_TILE_NAME: Final = "Copernicus_DSM_COG_10_S01_00_E117_00_DEM"

# Resolusi DEM dalam meter.
#
# Angka ini menentukan kerapatan pencuplikan profil medan. Mencuplik lebih jarang
# melewatkan puncak bukit — dan puncak bukit itulah yang jadi penghalang, yaitu
# hal yang justru ingin ditunjukkan peta ini.
#
# Sumber: spesifikasi produk Copernicus DEM GLO-30 (30 m).
DEM_RESOLUTION_M: Final = 30

# ---------------------------------------------------------------------------
# Sumber data — pemancar
# ---------------------------------------------------------------------------

# Cermin OpenCelliD di Internet Archive, terbitan 2017, lisensi CC BY-SA 3.0.
# Bisa diambil tanpa akun sama sekali. Cukup untuk membuktikan seluruh alur
# jalan, TERLALU TUA untuk peta yang dipamerkan — LTE-nya baru 2,5%.
#
# Sumber: docs/LANGKAH-0.md, syarat 1.
OPENCELLID_ARCHIVE_URL: Final = (
    "https://archive.org/download/opencellid_cell_towers.csv/cell_towers.csv.gz"
)

# Data terkini perlu token gratis dari opencellid.org. Token dibaca dari variabel
# lingkungan ini dan DILARANG masuk git — Prinsip VII. Kalau kosong, pengunduh
# berhenti dengan pesan yang menyebut nama variabelnya, bukan gagal diam-diam.
OPENCELLID_TOKEN_ENV: Final = "OPENCELLID_TOKEN"

# Urutan kolom CSV OpenCelliD. Dibaca langsung dari kepala berkasnya, bukan dari
# dokumentasi — dokumentasi bisa tertinggal, berkasnya tidak.
#
# Sumber: baris pertama cell_towers.csv, diperiksa 2026-08-14.
OPENCELLID_COLUMNS: Final = (
    "radio",
    "mcc",
    "net",
    "area",
    "cell",
    "unit",
    "lon",
    "lat",
    "range",
    "samples",
    "changeable",
    "created",
    "updated",
    "averageSignal",
)

# ---------------------------------------------------------------------------
# Kerincian hitung
# ---------------------------------------------------------------------------

# Mulai kasar, perhalus bertahap. PRD bagian 5 mewajibkan urutan ini: memulai
# langsung dari kerincian tertinggi berisiko menghabiskan berjam-jam sebelum
# ketahuan alurnya salah.
#
# 240 m = delapan kali resolusi DEM, sekitar 21.000 sel per operator.
#  30 m = setara resolusi DEM, sekitar 1.350.000 sel per operator.
#
# Sumber: specs/001-signal-prediction-map/research.md bagian 5.
COARSE_GRID_RESOLUTION_M: Final = 240
FINE_GRID_RESOLUTION_M: Final = 30

# ---------------------------------------------------------------------------
# Asumsi pemancar — BACA PERINGATAN INI
# ---------------------------------------------------------------------------
#
# Data terbuka menyimpan jenis radio, posisi, radius, dan jumlah cuplikan. Ia
# TIDAK menyimpan frekuensi, tinggi antena, daya pancar, arah, maupun kemiringan
# antena. Rumus propagasi membutuhkan semuanya.
#
# Jadi semua pemancar terpaksa dianggap sama. Akibatnya perbedaan antara satu
# lokasi dan lokasi lain datang hampir seluruhnya dari jarak dan bentuk tanah.
# Ini kemungkinan sumber kesalahan terbesar di seluruh peta — lebih besar
# daripada rumus propagasinya sendiri, dan itu sebabnya PRD bagian 7 poin 5 dan
# FR-024 mewajibkannya dinyatakan terang-terangan di halaman.
#
# Satu keringanan yang perlu dicatat: karena asumsi ini seragam untuk semua
# pemancar, EIRP bekerja sebagai geseran tetap. Ia menggeser seluruh peta naik
# atau turun bersama-sama, tanpa mengubah pola relatifnya. Jadi pertanyaan
# "operator mana yang lebih baik di daerah saya" jauh lebih tahan terhadap
# kesalahan angka ini daripada angka dBm yang ditampilkan saat titik ditekan.
#
# SUMBER SELURUH BAGIAN INI:
#   Report ITU-R M.2292-0 (12/2013), "Characteristics of terrestrial
#   IMT-Advanced systems for frequency sharing/interference analyses",
#   Tabel 2 (pita di bawah 1 GHz) dan Tabel 3 (pita 1-3 GHz), kolom
#   "Macro urban". Diambil dari itu.int, 14 Agustus 2026.

# Frekuensi yang diasumsikan per jenis jaringan, dalam MHz.
#
# INI PILIHAN, BUKAN FAKTA. Tiap teknologi dipakai di lebih dari satu pita di
# Indonesia; yang dipilih di sini adalah pita tempat teknologi itu paling banyak
# digelar:
#   GSM  -> 900   (band plan GSM-900; GSM juga ada di 1800)
#   UMTS -> 2100  (band plan IMT-2000, tempat izin 3G Indonesia diberikan)
#   LTE  -> 1800  (pita LTE terbesar di Indonesia pada masa data ini dikumpulkan)
#
# Frekuensi berpengaruh besar: redaman ruang bebas naik 20 log10(f), jadi selisih
# 900 dan 1800 MHz saja sudah 6 dB. Kalau nanti ada data yang menyebut pita
# sebenarnya per sel, angka ini yang pertama harus diganti.
#
# Sumber pita: rencana pita frekuensi Indonesia (GSM-900, GSM-1800, IMT-2000),
# Direktorat Jenderal Pos dan Telekomunikasi.

# Tinggi antena dan EIRP mengikuti pita tempat frekuensinya jatuh:
#   < 1 GHz   -> tinggi 30 m, EIRP/sektor 58 dBm dalam 10 MHz   (M.2292 Tabel 2)
#   1-2 GHz   -> tinggi 25 m, EIRP/sektor 59 dBm dalam 10 MHz   (M.2292 Tabel 3)
#   2-3 GHz   -> tinggi 20 m, EIRP/sektor 59 dBm dalam 10 MHz   (M.2292 Tabel 3)
#
# EIRP di sini sudah termasuk gain antena dan rugi feeder, jadi keduanya tidak
# dihitung lagi terpisah. Angka aslinya: daya keluaran 46 dBm dalam 10 MHz, gain
# antena maksimum 16 dBi (15 dBi untuk pita di bawah 1 GHz), rugi feeder 3 dB.
#
# EIRP yang dipakai adalah nilai PER SEKTOR, dan itu memang yang benar di sini:
# satu baris OpenCelliD adalah satu sel, yaitu satu sektor. Ponsel juga menempel
# ke satu sektor, bukan ke jumlah seluruh menara.
RADIO_ASSUMPTIONS: Final[dict[str, TransmitterAssumptions]] = {
    "GSM": TransmitterAssumptions(frequency_mhz=900, antenna_height_m=30, eirp_dbm=58),
    "UMTS": TransmitterAssumptions(frequency_mhz=2100, antenna_height_m=20, eirp_dbm=59),
    "LTE": TransmitterAssumptions(frequency_mhz=1800, antenna_height_m=25, eirp_dbm=59),
}

# Arah antena dianggap menyebar rata ke segala arah.
#
# Arah dan kemiringan sektor tidak diketahui, dan mengarang arah lebih buruk
# daripada mengabaikannya: arah yang salah memindahkan sinyal ke tempat yang
# keliru, sedangkan menganggap omni cuma melebihkan cakupan secara merata.
# Dipasangkan dengan EIRP per sektor, anggapan ini mendekati "sektor yang
# kebetulan menghadap ke titik ini" — yang memang sektor yang dipakai ponsel.
ANTENNA_IS_OMNIDIRECTIONAL: Final = True

# Tinggi penerima di atas tanah, meter. Ponsel dipegang orang yang berdiri.
#
# Sumber: 3GPP TR 38.901, skenario Urban Macro (UMa), tinggi terminal pengguna.
# Nilai yang sama dipakai luas di perkakas propagasi sebagai tinggi penerima
# bergerak.
RECEIVER_HEIGHT_M: Final = 1.5

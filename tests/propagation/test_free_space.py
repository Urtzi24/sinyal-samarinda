"""Tes angka acuan redaman ruang bebas.

Sumber: Recommendation ITU-R P.525-5 (11/2024), "Calculation of free-space
attenuation". Diambil dari itu.int, 14 Agustus 2026.

Rekomendasi itu memberi dua bentuk yang setara untuk besaran yang sama:

    pers. (5)   Lbf = 20 log10(4 pi d / lambda)      d dan lambda satuan sama
    pers. (6)   Lbf = 32,4 + 20 log10(f) + 20 log10(d)   f dalam MHz, d dalam km

Nilai acuan di berkas ini dihitung dari **pers. (6)**, sedangkan kodenya ditulis
dari **pers. (5)**. Itu disengaja: dua bentuk terbitan yang berbeda saling
memeriksa, sehingga salah ketik di salah satu sisi tidak bisa lolos diam-diam.
Menguji satu bentuk terhadap dirinya sendiri tidak membuktikan apa pun.
"""

import math

import numpy as np
import pytest

from dapur.propagation.free_space import free_space_loss_db

# Toleransi 0,01 dB. Longgar dibanding ketelitian float, tapi ketat dibanding
# ketelitian model mana pun — cukup untuk menangkap salah ketik, tidak cukup
# longgar untuk menyembunyikan kesalahan rumus.
TOLERANSI_DB = 0.01

# Tetapan 32,4 di pers. (6) adalah nilai TERBITAN YANG DIBULATKAN. Nilai
# eksaknya 20 log10(4 pi 1e9 / c) = 32,4478 dB. Selisih 0,05 dB itu milik
# pembulatan ITU, bukan milik kode — jadi perbandingan terhadap pers. (6) diberi
# ruang sebesar itu.
TOLERANSI_TETAPAN_TERBIT_DB = 0.05


def acuan_pers_6(frequency_mhz: float, distance_km: float) -> float:
    """Redaman ruang bebas menurut ITU-R P.525-5 pers. (6)."""
    return 32.4 + 20 * math.log10(frequency_mhz) + 20 * math.log10(distance_km)


@pytest.mark.parametrize(
    ("frequency_mhz", "distance_km"),
    [
        (900, 1),  # GSM, jarak sel khas
        (1800, 1),  # LTE
        (2100, 1),  # UMTS
        (900, 0.5),  # dekat menara
        (1800, 5),  # pinggir sel
        (2100, 20),  # sejauh batas penyaringan pemancar
    ],
)
def test_cocok_dengan_bentuk_frekuensi_itu(frequency_mhz: float, distance_km: float) -> None:
    """Bentuk panjang gelombang (pers. 5) harus setara bentuk frekuensi (pers. 6)."""
    hasil = free_space_loss_db(distance_m=distance_km * 1000, frequency_mhz=frequency_mhz)
    assert hasil == pytest.approx(
        acuan_pers_6(frequency_mhz, distance_km), abs=TOLERANSI_TETAPAN_TERBIT_DB
    )


def test_tetapan_terbitan_32_4_db() -> None:
    """Pada 1 MHz dan 1 km, pers. (6) menyusut jadi tetapannya sendiri: 32,4 dB.

    ITU menyebut angka ini redaman acuan pada 1 MHz sejauh 1 km. Kalau tes ini
    gagal, kemungkinan satuan tertukar — meter dengan kilometer, atau hertz
    dengan megahertz.
    """
    hasil = free_space_loss_db(distance_m=1000, frequency_mhz=1)
    assert hasil == pytest.approx(32.4, abs=TOLERANSI_TETAPAN_TERBIT_DB)


def test_jarak_berlipat_menambah_6_02_db() -> None:
    """Hukum kuadrat terbalik: jarak dua kali lipat menambah 20 log10(2) dB.

    Ini invarian fisika, bukan angka terbitan — ia tetap benar berapa pun
    tetapan yang dipakai, jadi ia menangkap kesalahan yang tidak tertangkap
    oleh perbandingan terhadap pers. (6).
    """
    dekat = free_space_loss_db(distance_m=1000, frequency_mhz=900)
    jauh = free_space_loss_db(distance_m=2000, frequency_mhz=900)
    assert jauh - dekat == pytest.approx(20 * math.log10(2), abs=TOLERANSI_DB)


def test_frekuensi_berlipat_menambah_6_02_db() -> None:
    """Frekuensi dua kali lipat juga menambah 20 log10(2) dB.

    Inilah sebabnya pemetaan jenis radio ke pita di dapur/constants.py penting:
    menebak 900 MHz padahal sebenarnya 1800 MHz meleset 6 dB di setiap titik.
    """
    rendah = free_space_loss_db(distance_m=1000, frequency_mhz=900)
    tinggi = free_space_loss_db(distance_m=1000, frequency_mhz=1800)
    assert tinggi - rendah == pytest.approx(20 * math.log10(2), abs=TOLERANSI_DB)


def test_menerima_larik_numpy() -> None:
    """Jutaan sel dihitung sekaligus, bukan satu per satu dengan perulangan.

    PRD bagian 9 memilih NumPy justru untuk ini. Fungsi yang cuma menerima
    skalar akan memaksa perulangan Python di kemudian hari.
    """
    jarak = np.array([1000.0, 2000.0, 4000.0])
    hasil = free_space_loss_db(distance_m=jarak, frequency_mhz=900)
    assert isinstance(hasil, np.ndarray)
    assert hasil.shape == jarak.shape
    selisih = np.diff(hasil)
    assert np.allclose(selisih, 20 * math.log10(2), atol=TOLERANSI_DB)


def test_jarak_nol_tidak_menghasilkan_tak_hingga_diam_diam() -> None:
    """Jarak nol tidak punya arti fisik dan wajib ditolak terang-terangan.

    Membiarkannya menghasilkan -inf berarti sel tepat di bawah menara membawa
    nilai yang merusak seluruh perhitungan di sekitarnya tanpa pesan apa pun.
    """
    with pytest.raises(ValueError):
        free_space_loss_db(distance_m=0, frequency_mhz=900)

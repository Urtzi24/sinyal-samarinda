"""Redaman ruang bebas menurut ITU-R P.525.

Fungsi murni. Tidak membaca berkas, tidak menyentuh jaringan, tidak membaca jam
sistem — Prinsip III.

Sumber: Recommendation ITU-R P.525-5 (11/2024), "Calculation of free-space
attenuation", persamaan (5):

    Lbf = 20 log10( 4 pi d / lambda )   dB

dengan d dan lambda dalam satuan yang sama.

Rekomendasi yang sama juga memberi bentuk setara dalam satuan praktis di
persamaan (6): Lbf = 32,4 + 20 log10(f_MHz) + 20 log10(d_km). Bentuk itu TIDAK
dipakai di sini — ia dipakai di tesnya, supaya dua bentuk terbitan yang berbeda
saling memeriksa alih-alih rumus menguji dirinya sendiri.
"""

import numpy as np

from dapur.constants import SPEED_OF_LIGHT_M_S

# Faktor 4 pi berasal dari luas permukaan bola: daya yang dipancarkan menyebar
# rata ke seluruh bola berjari-jari d. Bukan tetapan pilihan, jadi tidak punya
# sumber terpisah — ia bagian dari persamaan (5) itu sendiri.
FOUR_PI = 4.0 * np.pi

MHZ_TO_HZ = 1.0e6


def wavelength_m(frequency_mhz: float | np.ndarray) -> float | np.ndarray:
    """Panjang gelombang dalam meter untuk frekuensi dalam MHz."""
    if np.any(np.asarray(frequency_mhz) <= 0):
        raise ValueError("frekuensi harus lebih besar dari nol")
    return SPEED_OF_LIGHT_M_S / (np.asarray(frequency_mhz, dtype=float) * MHZ_TO_HZ)


def free_space_loss_db(
    distance_m: float | np.ndarray,
    frequency_mhz: float | np.ndarray,
) -> float | np.ndarray:
    """Redaman dasar ruang bebas dalam dB.

    Args:
        distance_m: jarak pemancar ke penerima, meter. Harus lebih besar dari nol.
        frequency_mhz: frekuensi, MHz.

    Raises:
        ValueError: kalau ada jarak nol atau negatif.

    Jarak nol ditolak terang-terangan, bukan dibiarkan menghasilkan minus tak
    hingga. Sel tepat di bawah menara akan membawa nilai rusak itu ke seluruh
    perhitungan di sekitarnya tanpa satu pun pesan galat.
    """
    distance = np.asarray(distance_m, dtype=float)
    if np.any(distance <= 0):
        raise ValueError("jarak harus lebih besar dari nol")

    wavelength = wavelength_m(frequency_mhz)
    loss = 20.0 * np.log10(FOUR_PI * distance / wavelength)

    # Masukan skalar keluar skalar, masukan larik keluar larik.
    if np.isscalar(distance_m) and np.isscalar(frequency_mhz):
        return float(loss)
    return loss

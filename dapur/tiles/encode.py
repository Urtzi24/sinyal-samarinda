"""Penyandian nilai sinyal ke piksel RGBA.

Fungsi murni.

Kontraknya di specs/001-signal-prediction-map/contracts/tile-format.md, dan
kedua sisi — Python di sini, TypeScript di etalase — wajib sepakat persis. Kalau
tidak, petanya tetap tampil; cuma angkanya salah, dan tidak ada yang tahu.

    R, G : nilai 16 bit = (dBm + 140) * 10
    B    : 0 = data tidak memadai, 255 = memadai
    A    : 0 = di luar batas kota, 255 = di dalam
"""

import numpy as np

# Pergeseran supaya daya terima yang selalu negatif jadi bilangan tak bernegatif.
DBM_OFFSET = 140.0

# Langkah 0,1 dB. Jauh lebih halus daripada ketelitian modelnya — disengaja,
# supaya penyandian tidak menambah galat sendiri. Yang ditampilkan ke pengguna
# tetap dibulatkan.
DBM_SCALE = 10.0

# Nilai terbesar yang muat: -140 dBm sampai +40 dBm.
VALUE_MAX = 1800

BYTE_MAX = 255
BITS_PER_BYTE = 8


def encode_dbm(power_dbm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ubah daya terima jadi pasangan kanal merah dan hijau.

    Nilai di luar jangkauan **dipangkas, bukan dilipat**. Melipat menghasilkan
    angka yang tampak wajar padahal salah — misalnya sinyal sangat lemah yang
    tiba-tiba terbaca sangat kuat.

    NaN disandikan sebagai nol dan diandalkan ditandai lewat kanal biru.
    """
    nilai = (np.asarray(power_dbm, dtype=float) + DBM_OFFSET) * DBM_SCALE
    nilai = np.where(np.isnan(nilai), 0.0, nilai)
    nilai = np.clip(np.rint(nilai), 0, VALUE_MAX).astype(np.uint16)
    return (nilai >> BITS_PER_BYTE).astype(np.uint8), (nilai & BYTE_MAX).astype(np.uint8)


def decode_rgb(red: np.ndarray, green: np.ndarray) -> np.ndarray:
    """Kebalikan `encode_dbm`. Dipakai tes, dan dicerminkan di etalase."""
    nilai = (np.asarray(red, dtype=np.uint16) << BITS_PER_BYTE) | np.asarray(green, dtype=np.uint16)
    return nilai.astype(float) / DBM_SCALE - DBM_OFFSET


def encode_tile(
    power_dbm: np.ndarray,
    data_adequate: np.ndarray,
    inside_city: np.ndarray,
) -> np.ndarray:
    """Susun satu ubin RGBA dari tiga larik sebentuk.

    Returns:
        Larik uint8 berbentuk (tinggi, lebar, 4).
    """
    red, green = encode_dbm(power_dbm)
    blue = np.where(np.asarray(data_adequate), BYTE_MAX, 0).astype(np.uint8)
    alpha = np.where(np.asarray(inside_city), BYTE_MAX, 0).astype(np.uint8)
    return np.stack([red, green, blue, alpha], axis=-1)

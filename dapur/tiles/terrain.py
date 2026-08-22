"""Penggambar ubin ketinggian tanah.

Fungsi murni terhadap masukannya.

Memakai penyandian **Terrarium** — standar terbuka yang dimengerti MapLibre
langsung, tanpa kunci dan tanpa layanan pihak ketiga:

    ketinggian_meter = (R * 256 + G + B / 256) - 32768

Kenapa bukan warna jadi: sama seperti ubin sinyal, yang disimpan nilainya,
supaya tampilannya bisa diubah tanpa menghitung ulang.
"""

import numpy as np

from dapur.grid.profile import ElevationSurface
from dapur.tiles.mercator import TILE_SIZE, pixel_centres

# Pergeseran Terrarium: memindahkan seluruh jangkauan ketinggian bumi, termasuk
# palung laut, ke bilangan tak bernegatif.
TERRARIUM_OFFSET_M = 32768.0

BYTE_RANGE = 256


def encode_terrarium(elevations_m: np.ndarray) -> np.ndarray:
    """Sandikan ketinggian jadi piksel RGBA Terrarium.

    Lubang data diisi nol — permukaan laut. Untuk bentang alam ini pilihan yang
    aman: laut memang datar, dan Samarinda dikelilingi sungai serta pesisir.
    """
    tinggi = np.nan_to_num(np.asarray(elevations_m, dtype=float), nan=0.0)
    nilai = np.clip(tinggi + TERRARIUM_OFFSET_M, 0, BYTE_RANGE**2 - 1 / BYTE_RANGE)

    red = np.floor(nilai / BYTE_RANGE).astype(np.uint8)
    green = np.floor(nilai % BYTE_RANGE).astype(np.uint8)
    blue = np.floor((nilai - np.floor(nilai)) * BYTE_RANGE).astype(np.uint8)
    alpha = np.full(red.shape, 255, dtype=np.uint8)
    return np.stack([red, green, blue, alpha], axis=-1)


def decode_terrarium(pixels: np.ndarray) -> np.ndarray:
    """Kebalikan `encode_terrarium`. Dipakai tes."""
    red = pixels[..., 0].astype(float)
    green = pixels[..., 1].astype(float)
    blue = pixels[..., 2].astype(float)
    return red * BYTE_RANGE + green + blue / BYTE_RANGE - TERRARIUM_OFFSET_M


def render_terrain_tile(
    surface: ElevationSurface,
    x: int,
    y: int,
    zoom: int,
    size: int = TILE_SIZE,
) -> np.ndarray:
    """Gambar satu ubin ketinggian."""
    lon, lat = pixel_centres(x, y, zoom, size)
    return encode_terrarium(surface.sample(lon, lat))

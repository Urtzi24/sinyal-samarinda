"""Matematika ubin peta Web Mercator.

Fungsi murni.

Ini sistem penomoran ubin yang dipakai hampir semua peta web: dunia dibagi jadi
satu ubin di zoom 0, lalu tiap naik satu zoom tiap ubin dibelah jadi empat.
"""

import math

import numpy as np

TILE_SIZE = 256

# Batas lintang Web Mercator. Di atas ini proyeksinya meregang tak hingga, jadi
# petanya dipotong. Samarinda ada di khatulistiwa, jauh dari batas ini.
MAX_LATITUDE_DEG = 85.05112878


def lonlat_to_tile(lon: float, lat: float, zoom: int) -> tuple[int, int]:
    """Ubin mana yang memuat satu titik lon/lat."""
    n = 2**zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(max(min(lat, MAX_LATITUDE_DEG), -MAX_LATITUDE_DEG))
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return max(min(x, n - 1), 0), max(min(y, n - 1), 0)


def tile_range(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float, zoom: int
) -> tuple[int, int, int, int]:
    """Rentang nomor ubin yang menutupi sebuah kotak batas.

    Returns:
        (x_min, y_min, x_max, y_max), semuanya inklusif.
    """
    x1, y1 = lonlat_to_tile(min_lon, max_lat, zoom)
    x2, y2 = lonlat_to_tile(max_lon, min_lat, zoom)
    return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)


def tile_bounds(x: int, y: int, zoom: int) -> tuple[float, float, float, float]:
    """Kotak batas satu ubin dalam derajat: (barat, selatan, timur, utara)."""
    n = 2**zoom
    west = x / n * 360.0 - 180.0
    east = (x + 1) / n * 360.0 - 180.0
    north = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    south = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return west, south, east, north


def pixel_centres(
    x: int, y: int, zoom: int, size: int = TILE_SIZE
) -> tuple[np.ndarray, np.ndarray]:
    """Koordinat lon/lat titik tengah tiap piksel dalam satu ubin.

    Titik tengah, bukan sudut — sama seperti kisi hitung. Memakai sudut membuat
    seluruh ubin bergeser setengah piksel.
    """
    n = 2**zoom
    kolom = (np.arange(size) + 0.5) / size
    baris = (np.arange(size) + 0.5) / size

    lon = (x + kolom) / n * 360.0 - 180.0
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * (y + baris) / n))))

    return np.meshgrid(lon, lat)

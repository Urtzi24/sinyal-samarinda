"""Pengambil profil medan dari raster ketinggian.

Membaca berkas raster. Tidak menyentuh jaringan.

Profil medan adalah irisan ketinggian sepanjang garis lurus dari pemancar ke
satu titik hitung. Inilah masukan perhitungan difraksi — tanpa profil, tidak ada
cara mengetahui bukit mana yang menghalangi.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling

from dapur.constants import DEM_RESOLUTION_M

# Batas jumlah titik cuplik per profil.
#
# Pencuplikan seharusnya serapat DEM (30 m) supaya puncak bukit tidak terlewat.
# Tapi lintasan 20 km berarti 666 titik, dan dikalikan jutaan pasangan
# pemancar-sel angkanya jadi mustahil. Batas ini memaksa lintasan panjang
# dicuplik lebih renggang.
#
# Akibatnya jujur: pada lintasan yang sangat panjang, bukit sempit bisa
# terlewat. Lintasan sepanjang itu sudah teredam berat oleh jarak, jadi
# pengaruhnya kecil — tapi ini penyederhanaan, bukan hal yang gratis.
MAX_PROFILE_SAMPLES = 128


@dataclass
class ElevationSurface:
    """Raster ketinggian yang sudah dimuat ke memori.

    Dimuat sekali lalu dipakai berulang. Membuka berkas untuk tiap profil akan
    membuat perhitungan seluruh kota berjam-jam lebih lama tanpa alasan.
    """

    elevations: np.ndarray
    transform: rasterio.Affine
    nodata: float | None
    crs: str

    @classmethod
    def load(cls, path: Path) -> "ElevationSurface":
        with rasterio.open(path) as src:
            data = src.read(1, resampling=Resampling.nearest).astype(float)
            return cls(
                elevations=data,
                transform=src.transform,
                nodata=src.nodata,
                crs=str(src.crs),
            )

    def sample(self, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
        """Ketinggian di titik-titik lon/lat, derajat.

        Nilai kosong (nodata) dikembalikan sebagai NaN, bukan nol. Laut setinggi
        nol dan data hilang adalah dua hal berbeda; menyamakannya membuat lubang
        data terbaca sebagai permukaan laut yang datar.
        """
        inv = ~self.transform
        col, row = inv * (np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))
        col = np.rint(col).astype(int)
        row = np.rint(row).astype(int)

        tinggi, lebar = self.elevations.shape
        di_dalam = (row >= 0) & (row < tinggi) & (col >= 0) & (col < lebar)

        hasil = np.full(np.shape(col), np.nan, dtype=float)
        hasil[di_dalam] = self.elevations[row[di_dalam], col[di_dalam]]

        if self.nodata is not None:
            hasil = np.where(hasil == self.nodata, np.nan, hasil)
        return hasil


def profile_sample_count(distance_m: float, step_m: float = DEM_RESOLUTION_M) -> int:
    """Berapa titik cuplik untuk lintasan sepanjang `distance_m`."""
    n = int(np.ceil(distance_m / step_m)) + 1
    return int(np.clip(n, 2, MAX_PROFILE_SAMPLES))


def terrain_profile(
    surface: ElevationSurface,
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
    distance_m: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Irisan ketinggian sepanjang garis lurus dari titik 1 ke titik 2.

    Args:
        surface: raster ketinggian yang sudah dimuat.
        lon1, lat1: ujung pertama, derajat.
        lon2, lat2: ujung kedua, derajat.
        distance_m: jarak sebenarnya antara kedua ujung, meter. Dihitung di
            sistem koordinat metrik, bukan dari selisih derajat.

    Returns:
        Pasangan (jarak dari ujung pertama dalam meter, ketinggian dalam meter).

    Lubang data diisi dengan ketinggian tetangga terdekat yang ada. Membiarkan
    NaN akan merambat ke seluruh perhitungan difraksi dan menghasilkan sel
    kosong yang tidak bisa dibedakan dari daerah tanpa sinyal.
    """
    n = profile_sample_count(distance_m)
    t = np.linspace(0.0, 1.0, n)

    lon = lon1 + (lon2 - lon1) * t
    lat = lat1 + (lat2 - lat1) * t
    elevations = surface.sample(lon, lat)

    if np.isnan(elevations).any():
        elevations = _isi_lubang(elevations)

    distances = t * distance_m
    return distances, elevations


def _isi_lubang(nilai: np.ndarray) -> np.ndarray:
    """Ganti NaN dengan nilai terdekat yang ada; nol kalau semuanya kosong."""
    ada = ~np.isnan(nilai)
    if not ada.any():
        return np.zeros_like(nilai)
    indeks = np.arange(nilai.size)
    return np.interp(indeks, indeks[ada], nilai[ada])

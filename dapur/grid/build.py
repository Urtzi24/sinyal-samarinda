"""Kisi hitung dan pengubahan koordinat.

Fungsi murni.

Semua perhitungan jarak dikerjakan dalam meter, bukan derajat. Menghitung jarak
langsung dari derajat itu salah: satu derajat bujur di khatulistiwa sekitar
111 km, dan menyusut ke nol di kutub. Karena itu koordinat dipindah ke sistem
proyeksi metrik lebih dulu.
"""

import math
from dataclasses import dataclass

import numpy as np
from pyproj import CRS, Transformer

from dapur.constants import BoundingBox

WGS84 = "EPSG:4326"

# Lebar satu zona UTM, derajat.
UTM_ZONE_WIDTH_DEG = 6.0

# Kode EPSG dasar untuk zona UTM di WGS84. Belahan utara mulai dari 32600,
# belahan selatan dari 32700; nomor zonanya ditambahkan ke angka itu.
EPSG_UTM_NORTH_BASE = 32600
EPSG_UTM_SOUTH_BASE = 32700


def utm_epsg_for(box: BoundingBox) -> str:
    """Pilih zona UTM yang cocok untuk sebuah kotak batas.

    Samarinda jatuh di zona 50 belahan selatan (EPSG:32750). Zona dipilih dari
    bujur tengah kotak, bukan ditulis mati, supaya kode ini tetap benar kalau
    suatu saat dipakai untuk kotak lain.
    """
    mid_lon = (box.min_lon + box.max_lon) / 2
    mid_lat = (box.min_lat + box.max_lat) / 2
    zone = int(math.floor((mid_lon + 180.0) / UTM_ZONE_WIDTH_DEG) + 1)
    base = EPSG_UTM_NORTH_BASE if mid_lat >= 0 else EPSG_UTM_SOUTH_BASE
    return f"EPSG:{base + zone}"


@dataclass(frozen=True)
class MetricProjection:
    """Pemindah koordinat antara derajat dan meter."""

    epsg: str

    def to_metric(self, lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        transformer = Transformer.from_crs(WGS84, CRS.from_user_input(self.epsg), always_xy=True)
        x, y = transformer.transform(lon, lat)
        return np.asarray(x, dtype=float), np.asarray(y, dtype=float)

    def to_degrees(self, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        transformer = Transformer.from_crs(CRS.from_user_input(self.epsg), WGS84, always_xy=True)
        lon, lat = transformer.transform(x, y)
        return np.asarray(lon, dtype=float), np.asarray(lat, dtype=float)


@dataclass(frozen=True)
class Grid:
    """Kisi hitung teratur, tersimpan dalam dua sistem koordinat sekaligus.

    Bentuknya dua dimensi (baris x kolom) supaya bisa langsung dipetakan ke
    piksel. Yang metrik dipakai menghitung jarak; yang derajat dipakai membaca
    DEM dan menulis ubin.
    """

    lon: np.ndarray
    lat: np.ndarray
    x_m: np.ndarray
    y_m: np.ndarray
    resolution_m: float
    projection: MetricProjection

    @property
    def shape(self) -> tuple[int, int]:
        return self.lon.shape  # type: ignore[return-value]

    def __len__(self) -> int:
        return int(self.lon.size)


def build_grid(box: BoundingBox, resolution_m: float) -> Grid:
    """Bangun kisi teratur berjarak `resolution_m` yang menutupi `box`.

    Args:
        box: kotak batas dalam derajat.
        resolution_m: jarak antar titik kisi, meter.

    Raises:
        ValueError: kalau resolusinya nol atau negatif.

    Titik kisi berada di TENGAH sel, bukan di sudutnya. Kalau di sudut, separuh
    sel di tepi kota jatuh di luar kotak dan pinggiran peta akan meleset separuh
    sel ke satu arah.
    """
    if resolution_m <= 0:
        raise ValueError("kerincian harus lebih besar dari nol")

    projection = MetricProjection(utm_epsg_for(box))

    sudut_lon = np.array([box.min_lon, box.max_lon, box.min_lon, box.max_lon])
    sudut_lat = np.array([box.min_lat, box.min_lat, box.max_lat, box.max_lat])
    x_sudut, y_sudut = projection.to_metric(sudut_lon, sudut_lat)

    x_min, x_max = float(x_sudut.min()), float(x_sudut.max())
    y_min, y_max = float(y_sudut.min()), float(y_sudut.max())

    kolom = max(math.ceil((x_max - x_min) / resolution_m), 1)
    baris = max(math.ceil((y_max - y_min) / resolution_m), 1)

    x_tengah = x_min + (np.arange(kolom) + 0.5) * resolution_m
    # Baris ditulis dari utara ke selatan supaya urutannya sama dengan piksel
    # citra, yang mulai dari kiri atas.
    y_tengah = y_max - (np.arange(baris) + 0.5) * resolution_m

    x_m, y_m = np.meshgrid(x_tengah, y_tengah)
    lon, lat = projection.to_degrees(x_m, y_m)

    return Grid(
        lon=lon,
        lat=lat,
        x_m=x_m,
        y_m=y_m,
        resolution_m=resolution_m,
        projection=projection,
    )

"""Penggambar ubin dari hasil hitung.

Fungsi murni terhadap masukannya; penulisan berkas ada di modul lain.

Hasil hitung tersimpan di kisi UTM, sedangkan ubin peta memakai Web Mercator.
Modul ini yang memindahkan nilainya: untuk tiap piksel ubin, cari sel kisi
terdekat lalu ambil nilainya.
"""

import numpy as np
import rasterio.features
from rasterio.transform import from_bounds

from dapur.grid.build import Grid
from dapur.propagation.received_power import Coverage
from dapur.tiles.encode import encode_tile
from dapur.tiles.mercator import TILE_SIZE, pixel_centres, tile_bounds


def _fractional_indices(grid: Grid, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Posisi titik metrik di dalam kisi, dalam satuan indeks berkoma.

    Kisinya teratur, jadi posisinya bisa dihitung langsung tanpa mencari — jauh
    lebih cepat daripada menelusuri jutaan sel satu per satu.
    """
    x0 = float(grid.x_m[0, 0])
    y0 = float(grid.y_m[0, 0])
    langkah = grid.resolution_m
    return (y0 - y) / langkah, (x - x0) / langkah


def _sample_bilinear(nilai: np.ndarray, baris: np.ndarray, kolom: np.ndarray) -> np.ndarray:
    """Ambil nilai kisi dengan pembobotan empat sel tetangga.

    Tanpa ini, tiap sel kisi tergambar sebagai kotak rata: pada zoom tinggi satu
    sel 60 m memenuhi belasan piksel layar, dan petanya terlihat bertangga.
    Dengan pembobotan, batas antar tingkat warna jadi berlekuk mengikuti bentuk
    medan yang sebenarnya.

    Yang dihaluskan NILAINYA, bukan warnanya. Tingkat warnanya tetap enam dan
    tetap tegas — kalau warnanya yang dicampur, akan muncul warna di luar skema
    dan tingkatannya berhenti bisa dibaca.
    """
    tinggi, lebar = nilai.shape
    b0 = np.clip(np.floor(baris).astype(int), 0, tinggi - 1)
    k0 = np.clip(np.floor(kolom).astype(int), 0, lebar - 1)
    b1 = np.clip(b0 + 1, 0, tinggi - 1)
    k1 = np.clip(k0 + 1, 0, lebar - 1)

    db = np.clip(baris - b0, 0.0, 1.0)
    dk = np.clip(kolom - k0, 0.0, 1.0)

    atas = nilai[b0, k0] * (1 - dk) + nilai[b0, k1] * dk
    bawah = nilai[b1, k0] * (1 - dk) + nilai[b1, k1] * dk
    campur = atas * (1 - db) + bawah * db

    # Sel tanpa hasil hitung tidak boleh menular ke tetangganya lewat
    # pembobotan. Kalau salah satu dari empat tetangga kosong, titik itu
    # dianggap kosong juga — lebih baik lubang jujur daripada angka karangan.
    kosong = (
        np.isnan(nilai[b0, k0])
        | np.isnan(nilai[b0, k1])
        | np.isnan(nilai[b1, k0])
        | np.isnan(nilai[b1, k1])
    )
    return np.where(kosong, np.nan, campur)


def city_mask(
    boundary_geojson: dict, x: int, y: int, zoom: int, size: int = TILE_SIZE
) -> np.ndarray:
    """Piksel mana di ubin ini yang berada di dalam batas kota."""
    west, south, east, north = tile_bounds(x, y, zoom)
    transform = from_bounds(west, south, east, north, size, size)
    return rasterio.features.geometry_mask(
        [boundary_geojson],
        out_shape=(size, size),
        transform=transform,
        invert=True,
    )


def render_signal_tile(
    coverage: Coverage,
    grid: Grid,
    boundary_geojson: dict,
    x: int,
    y: int,
    zoom: int,
    size: int = TILE_SIZE,
) -> np.ndarray | None:
    """Gambar satu ubin sinyal.

    Returns:
        Larik RGBA (size, size, 4), atau None kalau ubin ini seluruhnya di luar
        batas kota. Ubin kosong tidak ditulis sama sekali — menulisnya cuma
        menambah ukuran arsip tanpa menambah satu pun keterangan.
    """
    di_kota = city_mask(boundary_geojson, x, y, zoom, size)
    if not di_kota.any():
        return None

    lon, lat = pixel_centres(x, y, zoom, size)
    px, py = grid.projection.to_metric(lon, lat)
    baris, kolom = _fractional_indices(grid, px, py)

    tinggi, lebar = coverage.received_power_dbm.shape
    sah = (baris >= 0) & (baris <= tinggi - 1) & (kolom >= 0) & (kolom <= lebar - 1)

    daya = np.full((size, size), np.nan, dtype=float)
    memadai = np.zeros((size, size), dtype=bool)

    if sah.any():
        daya[sah] = _sample_bilinear(coverage.received_power_dbm, baris[sah], kolom[sah])
        # Kecukupan data TIDAK dihaluskan — ia keterangan ya-atau-tidak, bukan
        # besaran. Mencampurnya akan melahirkan wilayah "setengah terdata" yang
        # tidak punya arti apa pun.
        memadai[sah] = coverage.data_adequate[
            np.rint(baris[sah]).astype(int), np.rint(kolom[sah]).astype(int)
        ]

    # Sel tanpa hasil hitung ditandai lewat kanal biru, bukan lewat angka kecil.
    memadai &= ~np.isnan(daya)

    return encode_tile(daya, memadai, di_kota)

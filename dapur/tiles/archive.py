"""Penulis arsip PMTiles.

Menulis berkas.

PMTiles adalah satu berkas besar yang bisa dibaca sepotong-sepotong lewat
permintaan HTTP biasa. Inilah yang membuat peta jutaan titik bisa disajikan
tanpa server dan tanpa biaya — peramban cuma mengambil potongan yang sedang
dilihat.

Modul ini sengaja TIDAK dinamai `pmtiles.py` supaya tidak tertukar dengan
pustaka `pmtiles` yang dipakainya.
"""

import io
from pathlib import Path

import numpy as np
from PIL import Image
from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import write as pmtiles_write

# Derajat disimpan sebagai bilangan bulat berskala sepuluh juta di kepala
# berkas PMTiles. Itu bagian dari bentuk berkasnya, bukan pilihan kita.
DEGREE_SCALE = 10_000_000


def encode_png(pixels: np.ndarray) -> bytes:
    """Ubah larik RGBA jadi berkas PNG di memori.

    PNG dipilih karena tanpa kehilangan data. Sandi nilai sinyal ada di dalam
    warnanya; format seperti JPEG akan mengubah warna sedikit demi menghemat
    ukuran, dan perubahan sedikit itu berarti angka sinyal yang salah.
    """
    penyangga = io.BytesIO()
    Image.fromarray(pixels, mode="RGBA").save(penyangga, format="PNG", optimize=True)
    return penyangga.getvalue()


class TileArchive:
    """Pengumpul ubin yang menuliskannya jadi satu arsip PMTiles.

    Ubin dikumpulkan dulu di memori lalu ditulis berurutan saat ditutup, karena
    PMTiles menyimpan ubin terurut menurut nomornya. Untuk Samarinda jumlahnya
    beberapa ribu — cukup kecil untuk ditahan di memori.

    Bisa menampung ubin gambar (PNG) maupun ubin vektor (MVT); yang membedakan
    cuma dua keterangan di kepala arsipnya.
    """

    def __init__(
        self,
        target: Path,
        bounds: tuple[float, float, float, float],
        *,
        tile_type: TileType = TileType.PNG,
        compression: Compression = Compression.NONE,
    ) -> None:
        self.target = target
        self.bounds = bounds
        self.tile_type = tile_type
        self.compression = compression
        self._tiles: dict[int, bytes] = {}

    def add(self, zoom: int, x: int, y: int, png_bytes: bytes) -> None:
        self._tiles[zxy_to_tileid(zoom, x, y)] = png_bytes

    def __len__(self) -> int:
        return len(self._tiles)

    @property
    def total_bytes(self) -> int:
        return sum(len(b) for b in self._tiles.values())

    def save(self, min_zoom: int, max_zoom: int) -> Path:
        """Tulis arsipnya ke cakram.

        Raises:
            ValueError: kalau tidak ada satu pun ubin. Arsip kosong akan tampil
                sebagai peta hitam tanpa pesan galat.
        """
        if not self._tiles:
            raise ValueError(f"{self.target.name}: tidak ada ubin untuk ditulis")

        west, south, east, north = self.bounds
        self.target.parent.mkdir(parents=True, exist_ok=True)

        with pmtiles_write(str(self.target)) as penulis:
            for tileid in sorted(self._tiles):
                penulis.write_tile(tileid, self._tiles[tileid])

            penulis.finalize(
                {
                    "tile_type": self.tile_type,
                    "tile_compression": self.compression,
                    "min_zoom": min_zoom,
                    "max_zoom": max_zoom,
                    "min_lon_e7": int(west * DEGREE_SCALE),
                    "min_lat_e7": int(south * DEGREE_SCALE),
                    "max_lon_e7": int(east * DEGREE_SCALE),
                    "max_lat_e7": int(north * DEGREE_SCALE),
                    "center_zoom": min_zoom,
                    "center_lon_e7": int((west + east) / 2 * DEGREE_SCALE),
                    "center_lat_e7": int((south + north) / 2 * DEGREE_SCALE),
                },
                {"nama": self.target.stem},
            )
        return self.target

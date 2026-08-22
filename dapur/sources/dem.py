"""Pengunduh ubin ketinggian Copernicus DEM GLO-30.

Menyentuh jaringan. Tidak boleh dipanggil dari mana pun di `dapur/propagation/`
— Prinsip III.

Seluruh Kota Samarinda muat dalam satu ubin 1 derajat x 1 derajat, sekitar 23 MB.
Tanpa akun, tanpa kunci API. Sudah diperiksa langsung di Langkah 0.
"""

from pathlib import Path

from dapur.constants import DEM_BASE_URL, DEM_TILE_NAME
from dapur.sources.fetch import download_file


def dem_tile_url() -> str:
    """Alamat ubin DEM yang menutupi Samarinda."""
    return f"{DEM_BASE_URL}/{DEM_TILE_NAME}/{DEM_TILE_NAME}.tif"


def download_dem(dest_dir: Path, *, force: bool = False) -> Path:
    """Unduh ubin ketinggian ke `dest_dir`.

    Args:
        dest_dir: folder tujuan, biasanya `data/mentah/`.
        force: unduh ulang walau berkasnya sudah ada.

    Returns:
        Jalur berkas GeoTIFF hasil unduhan.

    Berkas yang sudah ada dilewati — Prinsip IV. Mengunduh ulang 23 MB tiap kali
    dapur dijalankan cuma membuang waktu dan pita.
    """
    target = dest_dir / f"{DEM_TILE_NAME}.tif"
    return download_file(dem_tile_url(), target, force=force, label="ubin ketinggian")

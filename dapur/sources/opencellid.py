"""Pengunduh data pemancar OpenCelliD.

Menyentuh jaringan.

Dua sumber, dan bedanya penting:

**Arsip** — cermin di Internet Archive, terbitan 2017, tanpa akun sama sekali.
Cukup untuk membangun dan menguji seluruh alur. TERLALU TUA untuk peta yang
dipamerkan: LTE-nya baru 2,5%, dan sejak itu dua penggabungan operator sudah
terjadi.

**Terkini** — perlu token gratis dari opencellid.org. Token dibaca dari variabel
lingkungan, tidak pernah dari kode — Prinsip VII.
"""

import os
from pathlib import Path

from dapur.constants import OPENCELLID_ARCHIVE_URL, OPENCELLID_TOKEN_ENV
from dapur.sources.fetch import download_file

ARCHIVE_FILENAME = "cell_towers_2017.csv.gz"
CURRENT_FILENAME = "cell_towers_terkini.csv.gz"

# Titik akhir unduhan basis data penuh OpenCelliD. Memerlukan token.
CURRENT_URL = (
    "https://opencellid.org/ocid/downloads?token={token}&type=full&file=cell_towers.csv.gz"
)


class MissingTokenError(RuntimeError):
    """Data terkini diminta tapi tokennya tidak disetel."""


def read_token() -> str:
    """Baca token OpenCelliD dari variabel lingkungan.

    Raises:
        MissingTokenError: kalau variabelnya kosong atau tidak ada.

    Gagal terang-terangan dengan menyebut nama variabelnya dan cara
    mendapatkannya. Tidak ada token contoh di dalam kode, dan tidak ada
    kegagalan diam-diam yang menyisakan berkas kosong.
    """
    token = os.environ.get(OPENCELLID_TOKEN_ENV, "").strip()
    if not token:
        raise MissingTokenError(
            f"Variabel lingkungan {OPENCELLID_TOKEN_ENV} belum disetel.\n"
            "Data terkini OpenCelliD memerlukan token gratis:\n"
            "  1. Buat akun di https://opencellid.org\n"
            "  2. Salin token dari tab 'API Access Tokens'\n"
            f"  3. Setel {OPENCELLID_TOKEN_ENV} di lingkungan, JANGAN di dalam kode\n"
            "\n"
            "Untuk mencoba tanpa akun, pakai sumber 'arsip' — data 2017, cukup "
            "untuk membuktikan alurnya jalan."
        )
    return token


def download_archive(dest_dir: Path, *, force: bool = False) -> Path:
    """Unduh cermin 2017 dari Internet Archive. Tanpa akun."""
    print("  CATATAN: sumber arsip terbitan 2017. Cukup untuk menguji alur,")
    print("           terlalu tua untuk peta yang dipamerkan.")
    return download_file(
        OPENCELLID_ARCHIVE_URL,
        dest_dir / ARCHIVE_FILENAME,
        force=force,
        label="pemancar (arsip 2017)",
    )


def download_current(dest_dir: Path, *, force: bool = False) -> Path:
    """Unduh basis data terkini. Perlu token di variabel lingkungan.

    Raises:
        MissingTokenError: kalau tokennya belum disetel.
    """
    token = read_token()
    return download_file(
        CURRENT_URL.format(token=token),
        dest_dir / CURRENT_FILENAME,
        force=force,
        label="pemancar (terkini)",
    )

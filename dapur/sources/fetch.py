"""Pengambilan data dari jaringan, dipakai semua sumber.

Dipisah ke berkas sendiri supaya aturan "hanya langkah unduh yang boleh
menyentuh jaringan" bisa diperiksa dengan mata: kalau ada modul di luar
`dapur/sources/` yang mengimpor ini, aturannya sedang dilanggar.
"""

import json
import shutil
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Berkas yang lebih kecil dari ini hampir pasti halaman galat, bukan data.
# Ubin DEM 23 MB dan arsip OpenCelliD 707 MB; keduanya jauh di atas ambang ini.
SUSPICIOUSLY_SMALL_BYTES = 10_000

CHUNK_BYTES = 1024 * 256

BYTES_PER_MB = 1_048_576


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OVERPASS_TIMEOUT_S = 240

# Overpass menolak permintaan tanpa identitas dengan HTTP 406, dan penolakannya
# tidak menyebut alasan. Python tidak mengirim User-Agent sendiri.
USER_AGENT = "sinyal-samarinda/0.1 (peta prediksi sinyal Kota Samarinda)"

# Nomor area Overpass dibentuk dengan menambahkan angka ini ke nomor relasinya.
# Itu aturan Overpass, bukan pilihan kita.
OVERPASS_AREA_OFFSET = 3_600_000_000


class DownloadError(RuntimeError):
    """Unduhan tidak menghasilkan berkas yang bisa dipakai."""


def skip_if_exists(target: Path, label: str, *, force: bool) -> bool:
    """Benar kalau berkasnya sudah ada dan tidak diminta dibuat ulang."""
    if target.exists() and not force:
        print(f"  {label}: sudah ada, dilewati")
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    return False


def overpass_json(query: str, label: str) -> dict:
    """Jalankan satu kueri Overpass, kembalikan jawabannya.

    Raises:
        DownloadError: kalau jaringannya gagal atau jawabannya bukan JSON.
    """
    permintaan = urllib.request.Request(
        OVERPASS_URL,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(permintaan, timeout=OVERPASS_TIMEOUT_S) as respons:
            return json.load(respons)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as galat:
        raise DownloadError(f"{label}: gagal mengambil dari Overpass - {galat}") from galat


def overpass_area(relation_id: int) -> int:
    """Nomor area Overpass untuk sebuah relasi OpenStreetMap."""
    return OVERPASS_AREA_OFFSET + relation_id


def download_file(url: str, target: Path, *, force: bool = False, label: str = "berkas") -> Path:
    """Unduh `url` ke `target`, lewati kalau sudah ada.

    Args:
        url: alamat sumber.
        target: jalur berkas hasil unduhan.
        force: unduh ulang walau berkasnya sudah ada.
        label: sebutan untuk pesan di layar.

    Raises:
        DownloadError: kalau jaringan gagal atau hasilnya terlalu kecil untuk
            masuk akal.

    Berkas ditulis ke nama sementara lebih dulu, baru dipindahkan setelah utuh.
    Tanpa itu, unduhan yang terputus di tengah meninggalkan berkas separuh yang
    pada jalan berikutnya akan dikira sudah selesai — dan dapur akan menghitung
    di atas data yang terpotong tanpa satu pun peringatan.
    """
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not force:
        size = target.stat().st_size
        print(f"  {label}: sudah ada, dilewati ({size / BYTES_PER_MB:.1f} MB)")
        return target

    partial = target.with_suffix(target.suffix + ".sedang-diunduh")
    print(f"  {label}: mengunduh dari {url}")

    try:
        with urllib.request.urlopen(url) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out, CHUNK_BYTES)
    except (urllib.error.URLError, OSError) as error:
        partial.unlink(missing_ok=True)
        raise DownloadError(f"{label}: gagal mengunduh dari {url} — {error}") from error

    size = partial.stat().st_size
    if size < SUSPICIOUSLY_SMALL_BYTES:
        partial.unlink(missing_ok=True)
        raise DownloadError(
            f"{label}: hasil unduhan cuma {size} bita, terlalu kecil untuk data. "
            "Kemungkinan yang terunduh halaman galat, bukan berkasnya."
        )

    partial.replace(target)
    print(f"  {label}: selesai, {size / BYTES_PER_MB:.1f} MB")
    return target

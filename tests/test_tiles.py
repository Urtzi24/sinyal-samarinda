"""Tes penyandian ubin, matematika ubin peta, dan penulisan arsip."""

from pathlib import Path

import numpy as np
import pytest

from dapur.constants import SAMARINDA_BBOX
from dapur.tiles.archive import TileArchive, encode_png
from dapur.tiles.encode import DBM_OFFSET, VALUE_MAX, decode_rgb, encode_dbm, encode_tile
from dapur.tiles.mercator import TILE_SIZE, lonlat_to_tile, pixel_centres, tile_bounds, tile_range
from dapur.tiles.terrain import decode_terrarium, encode_terrarium

# Ketelitian penyandian: 0,1 dB per langkah, jadi galat bulat paling besar
# separuh langkah.
TOLERANSI_DB = 0.05


def test_pulang_pergi_seluruh_jangkauan() -> None:
    """Sandi dan baca harus mengembalikan angka yang sama, -140 sampai +40 dBm.

    Ini kontrak antara Python dan TypeScript. Kalau salah satu sisi bergeser,
    petanya tetap tampil — cuma angkanya salah, dan tidak ada yang tahu.
    """
    asli = np.arange(-140.0, 40.0, 0.1)
    merah, hijau = encode_dbm(asli)
    kembali = decode_rgb(merah, hijau)
    assert np.allclose(kembali, asli, atol=TOLERANSI_DB)


def test_nilai_di_luar_jangkauan_dipangkas_bukan_dilipat() -> None:
    """Melipat menghasilkan angka yang tampak wajar padahal salah.

    Sinyal -200 dBm yang melipat bisa terbaca sebagai sinyal sangat kuat, dan
    itu akan terlihat masuk akal di peta.
    """
    merah, hijau = encode_dbm(np.array([-500.0, 500.0]))
    nilai = (merah.astype(int) << 8) | hijau.astype(int)
    assert nilai[0] == 0
    assert nilai[1] == VALUE_MAX


def test_nan_tidak_meledak() -> None:
    """Sel tanpa hasil hitung disandikan nol dan ditandai lewat kanal biru."""
    merah, hijau = encode_dbm(np.array([np.nan]))
    assert merah[0] == 0
    assert hijau[0] == 0


def test_nilai_terlemah_jadi_nol() -> None:
    merah, hijau = encode_dbm(np.array([-DBM_OFFSET]))
    assert (int(merah[0]) << 8) | int(hijau[0]) == 0


def test_kanal_biru_menandai_kecukupan_data() -> None:
    """FR-011: 'data tidak memadai' wajib bisa dibedakan dari 'sinyal lemah'."""
    ubin = encode_tile(
        power_dbm=np.array([[-90.0, -90.0]]),
        data_adequate=np.array([[True, False]]),
        inside_city=np.array([[True, True]]),
    )
    assert ubin[0, 0, 2] == 255
    assert ubin[0, 1, 2] == 0
    # Dayanya sama; yang membedakan cuma kanal birunya.
    assert ubin[0, 0, 0] == ubin[0, 1, 0]


def test_kanal_alfa_menandai_luar_kota() -> None:
    ubin = encode_tile(
        power_dbm=np.array([[-90.0, -90.0]]),
        data_adequate=np.array([[True, True]]),
        inside_city=np.array([[True, False]]),
    )
    assert ubin[0, 0, 3] == 255
    assert ubin[0, 1, 3] == 0


def test_bentuk_ubin_rgba() -> None:
    ubin = encode_tile(
        power_dbm=np.zeros((4, 4)),
        data_adequate=np.ones((4, 4), dtype=bool),
        inside_city=np.ones((4, 4), dtype=bool),
    )
    assert ubin.shape == (4, 4, 4)
    assert ubin.dtype == np.uint8


# ---------------------------------------------------------------------------
# Ubin ketinggian
# ---------------------------------------------------------------------------


def test_pulang_pergi_terrarium() -> None:
    asli = np.array([[-100.0, 0.0, 50.0, 1500.0, 8848.0]])
    kembali = decode_terrarium(encode_terrarium(asli))
    assert np.allclose(kembali, asli, atol=0.01)


def test_terrarium_nodata_jadi_permukaan_laut() -> None:
    kembali = decode_terrarium(encode_terrarium(np.array([[np.nan]])))
    assert kembali[0, 0] == pytest.approx(0.0, abs=0.01)


# ---------------------------------------------------------------------------
# Matematika ubin peta
# ---------------------------------------------------------------------------


def test_samarinda_jatuh_di_ubin_yang_benar() -> None:
    """Zoom 0 cuma punya satu ubin; seluruh dunia ada di 0/0."""
    assert lonlat_to_tile(117.15, -0.5, 0) == (0, 0)


def test_batas_ubin_zoom_nol_seluruh_dunia() -> None:
    west, south, east, north = tile_bounds(0, 0, 0)
    assert west == pytest.approx(-180.0)
    assert east == pytest.approx(180.0)
    assert north == pytest.approx(85.05, abs=0.01)
    assert south == pytest.approx(-85.05, abs=0.01)


def test_rentang_ubin_menutupi_samarinda() -> None:
    x1, y1, x2, y2 = tile_range(
        SAMARINDA_BBOX.min_lon,
        SAMARINDA_BBOX.min_lat,
        SAMARINDA_BBOX.max_lon,
        SAMARINDA_BBOX.max_lat,
        zoom=14,
    )
    assert x1 <= x2
    assert y1 <= y2
    # Kotak Samarinda sekitar 27 x 45 km; di zoom 14 satu ubin sekitar 2,4 km.
    assert 8 <= (x2 - x1 + 1) <= 16
    assert 14 <= (y2 - y1 + 1) <= 24


def test_titik_tengah_piksel_ada_di_dalam_ubin() -> None:
    """Titik tengah, bukan sudut — sama seperti kisi hitung."""
    z, x, y = 14, 12800, 8200
    west, south, east, north = tile_bounds(x, y, z)
    lon, lat = pixel_centres(x, y, z)
    assert lon.shape == (TILE_SIZE, TILE_SIZE)
    assert lon.min() > west
    assert lon.max() < east
    assert lat.min() > south
    assert lat.max() < north


# ---------------------------------------------------------------------------
# Arsip
# ---------------------------------------------------------------------------


def ubin_contoh() -> bytes:
    piksel = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype=np.uint8)
    piksel[..., 3] = 255
    return encode_png(piksel)


def test_png_terbaca_sebagai_png() -> None:
    data = ubin_contoh()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_arsip_kosong_ditolak(tmp_path: Path) -> None:
    """Arsip kosong akan tampil sebagai peta hitam tanpa pesan galat."""
    arsip = TileArchive(tmp_path / "kosong.pmtiles", (117.0, -0.7, 117.3, -0.3))
    with pytest.raises(ValueError, match="tidak ada ubin"):
        arsip.save(min_zoom=10, max_zoom=14)


def test_arsip_tertulis_dan_terbaca_sebagai_pmtiles(tmp_path: Path) -> None:
    arsip = TileArchive(tmp_path / "uji.pmtiles", (117.0, -0.7, 117.3, -0.3))
    png = ubin_contoh()
    for x in range(2):
        for y in range(2):
            arsip.add(zoom=10, x=800 + x, y=500 + y, png_bytes=png)

    assert len(arsip) == 4
    assert arsip.total_bytes == len(png) * 4

    jalur = arsip.save(min_zoom=10, max_zoom=10)
    assert jalur.exists()
    assert jalur.read_bytes()[:7] == b"PMTiles"

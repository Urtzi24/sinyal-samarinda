"""Tes kisi hitung dan profil medan."""

import numpy as np
import pytest
import rasterio

from dapur.constants import SAMARINDA_BBOX, BoundingBox
from dapur.grid.build import build_grid, utm_epsg_for
from dapur.grid.profile import (
    MAX_PROFILE_SAMPLES,
    ElevationSurface,
    profile_sample_count,
    terrain_profile,
)


def test_zona_utm_samarinda() -> None:
    """Samarinda ada di zona UTM 50 belahan selatan."""
    assert utm_epsg_for(SAMARINDA_BBOX) == "EPSG:32750"


def test_zona_utm_ikut_belahan_bumi() -> None:
    """Kotak di utara khatulistiwa harus memakai kode zona utara."""
    utara = BoundingBox(min_lon=117.0, min_lat=1.0, max_lon=117.3, max_lat=2.0)
    assert utm_epsg_for(utara) == "EPSG:32650"


def test_jarak_antar_titik_sesuai_kerincian() -> None:
    """Titik kisi bersebelahan harus berjarak persis satu kerincian."""
    grid = build_grid(SAMARINDA_BBOX, resolution_m=1000)
    d_x = np.diff(grid.x_m[0, :])
    d_y = np.diff(grid.y_m[:, 0])
    assert np.allclose(d_x, 1000)
    assert np.allclose(d_y, -1000)  # baris berjalan dari utara ke selatan


def test_kisi_menutupi_seluruh_kotak() -> None:
    """Tidak boleh ada bagian kota yang jatuh di luar kisi.

    Diperiksa terhadap tepi SEL, bukan terhadap titik tengahnya. Titik tengah
    memang tidak pernah mencapai tepi kotak — itu bukan lubang, cuma akibat
    titik ditaruh di tengah sel.
    """
    kerincian = 500.0
    grid = build_grid(SAMARINDA_BBOX, resolution_m=kerincian)
    setengah = kerincian / 2

    sudut_lon = np.array([SAMARINDA_BBOX.min_lon, SAMARINDA_BBOX.max_lon] * 2)
    sudut_lat = np.array([SAMARINDA_BBOX.min_lat] * 2 + [SAMARINDA_BBOX.max_lat] * 2)
    x, y = grid.projection.to_metric(sudut_lon, sudut_lat)

    assert grid.x_m.min() - setengah <= x.min()
    assert grid.x_m.max() + setengah >= x.max()
    assert grid.y_m.min() - setengah <= y.min()
    assert grid.y_m.max() + setengah >= y.max()


def test_titik_di_tengah_sel_bukan_di_sudut() -> None:
    """Titik pertama harus setengah kerincian dari tepi, bukan di tepinya.

    Kalau di sudut, separuh sel di tepi kota jatuh di luar kotak dan seluruh
    peta bergeser setengah sel ke satu arah.
    """
    kerincian = 1000.0
    grid = build_grid(SAMARINDA_BBOX, resolution_m=kerincian)
    x_sudut, _ = grid.projection.to_metric(
        np.array([SAMARINDA_BBOX.min_lon]), np.array([SAMARINDA_BBOX.min_lat])
    )
    selisih = float(grid.x_m[0, 0]) - float(x_sudut[0])
    assert selisih > 0
    assert selisih < kerincian


def test_kerincian_lebih_halus_menghasilkan_lebih_banyak_sel() -> None:
    kasar = build_grid(SAMARINDA_BBOX, resolution_m=1000)
    halus = build_grid(SAMARINDA_BBOX, resolution_m=250)
    assert len(halus) > len(kasar) * 10


def test_kerincian_nol_ditolak() -> None:
    with pytest.raises(ValueError, match="kerincian"):
        build_grid(SAMARINDA_BBOX, resolution_m=0)


def test_pulang_pergi_koordinat() -> None:
    """Derajat ke meter lalu kembali harus menghasilkan titik yang sama."""
    grid = build_grid(SAMARINDA_BBOX, resolution_m=2000)
    lon, lat = grid.projection.to_degrees(grid.x_m, grid.y_m)
    assert np.allclose(lon, grid.lon, atol=1e-9)
    assert np.allclose(lat, grid.lat, atol=1e-9)


# ---------------------------------------------------------------------------
# Profil medan
# ---------------------------------------------------------------------------


def permukaan_datar(tinggi: float = 0.0, nodata: float | None = None) -> ElevationSurface:
    """Raster ketinggian buatan yang menutupi Samarinda."""
    data = np.full((100, 100), tinggi, dtype=float)
    transform = rasterio.Affine(0.005, 0.0, 117.0, 0.0, -0.005, -0.3)
    return ElevationSurface(elevations=data, transform=transform, nodata=nodata, crs="EPSG:4326")


def test_jumlah_cuplik_dibatasi() -> None:
    """Lintasan panjang tidak boleh menghasilkan ribuan titik cuplik."""
    assert profile_sample_count(200.0) >= 2
    assert profile_sample_count(1_000_000.0) == MAX_PROFILE_SAMPLES


def test_profil_berakhir_di_jarak_yang_diberikan() -> None:
    jarak, tinggi = terrain_profile(permukaan_datar(50.0), 117.1, -0.4, 117.2, -0.5, 15_000.0)
    assert jarak[0] == 0.0
    assert jarak[-1] == pytest.approx(15_000.0)
    assert len(jarak) == len(tinggi)


def test_profil_di_permukaan_datar_rata() -> None:
    _, tinggi = terrain_profile(permukaan_datar(75.0), 117.1, -0.4, 117.2, -0.5, 15_000.0)
    assert np.allclose(tinggi, 75.0)


def test_nodata_tidak_dianggap_permukaan_laut() -> None:
    """Data hilang dan laut setinggi nol adalah dua hal berbeda.

    Menyamakannya membuat lubang data terbaca sebagai dataran rata — dan
    dataran rata palsu itu akan terlihat seperti daerah bersinyal bagus.
    """
    permukaan = permukaan_datar(0.0, nodata=0.0)
    contoh = permukaan.sample(np.array([117.1]), np.array([-0.4]))
    assert np.isnan(contoh[0])


def test_titik_di_luar_raster_jadi_nan() -> None:
    permukaan = permukaan_datar(50.0)
    contoh = permukaan.sample(np.array([100.0]), np.array([50.0]))
    assert np.isnan(contoh[0])


def test_lubang_data_diisi_bukan_dibiarkan_nan() -> None:
    """NaN yang lolos akan merambat ke seluruh perhitungan difraksi."""
    data = np.full((100, 100), 40.0, dtype=float)
    data[40:60, 40:60] = -9999.0
    permukaan = ElevationSurface(
        elevations=data,
        transform=rasterio.Affine(0.005, 0.0, 117.0, 0.0, -0.005, -0.3),
        nodata=-9999.0,
        crs="EPSG:4326",
    )
    _, tinggi = terrain_profile(permukaan, 117.05, -0.35, 117.45, -0.75, 60_000.0)
    assert not np.isnan(tinggi).any()

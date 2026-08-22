"""Tes perangkai daya terima."""

import numpy as np
import pytest
import rasterio

from dapur.constants import BoundingBox
from dapur.grid.build import build_grid
from dapur.grid.profile import ElevationSurface
from dapur.propagation.free_space import free_space_loss_db
from dapur.propagation.received_power import DATA_ADEQUATE_RADIUS_M, compute_coverage
from dapur.sources.transmitters import TransmitterSet

# Kotak kecil supaya tesnya cepat.
KOTAK = BoundingBox(min_lon=117.10, min_lat=-0.55, max_lon=117.20, max_lat=-0.45)

EIRP_DBM = 59.0
FREKUENSI_MHZ = 1800.0
TINGGI_ANTENA_M = 25.0


def permukaan_datar(tinggi: float = 0.0) -> ElevationSurface:
    data = np.full((200, 200), tinggi, dtype=float)
    transform = rasterio.Affine(0.005, 0.0, 117.0, 0.0, -0.005, -0.3)
    return ElevationSurface(elevations=data, transform=transform, nodata=None, crs="EPSG:4326")


def satu_pemancar(lon: float, lat: float) -> TransmitterSet:
    return TransmitterSet(
        lon=np.array([lon]),
        lat=np.array([lat]),
        operator_id=np.array(["telkomsel"], dtype=object),
        frequency_mhz=np.array([FREKUENSI_MHZ]),
        antenna_height_m=np.array([TINGGI_ANTENA_M]),
        eirp_dbm=np.array([EIRP_DBM]),
    )


def test_tanpa_pemancar_semua_nan() -> None:
    """Operator tanpa satu pun pemancar terdata bukan berarti sinyalnya nol."""
    grid = build_grid(KOTAK, resolution_m=2000)
    kosong = np.array([])
    hasil = compute_coverage(
        grid,
        TransmitterSet(kosong, kosong, kosong, kosong, kosong, kosong),
        permukaan_datar(),
    )
    assert np.isnan(hasil.received_power_dbm).all()
    assert not hasil.data_adequate.any()


def test_medan_datar_sama_dengan_ruang_bebas() -> None:
    """Tanpa bukit, daya terima persis EIRP dikurangi redaman ruang bebas.

    Jaraknya MIRING, bukan mendatar: antena ada di ketinggian, jadi sel di
    bawahnya tetap berjarak setinggi antena itu.
    """
    grid = build_grid(KOTAK, resolution_m=2000)
    pemancar = satu_pemancar(117.15, -0.50)
    hasil = compute_coverage(grid, pemancar, permukaan_datar())

    tx_x, tx_y = grid.projection.to_metric(pemancar.lon, pemancar.lat)
    mendatar = np.hypot(grid.x_m - tx_x[0], grid.y_m - tx_y[0])
    jarak = np.hypot(mendatar, TINGGI_ANTENA_M - 1.5)
    harapan = EIRP_DBM - np.asarray(free_space_loss_db(jarak, FREKUENSI_MHZ))

    assert np.allclose(hasil.received_power_dbm, harapan, atol=0.01)


def test_sel_di_bawah_menara_memakai_jarak_miring() -> None:
    """Sel tepat di bawah antena berjarak setinggi antena, bukan nol.

    Versi pertama memakai jarak mendatar, jadi sel di bawah menara dianggap
    berjarak satu meter dan menghasilkan +13 dBm — dua puluh milliwatt sampai
    di ponsel, mustahil. Tes kisi kasar tidak menangkapnya karena sel
    terdekatnya 1.000 m dari menara, dan di jarak itu selisih miring cuma
    0,002 dB. Kesalahannya hanya muncul di dekat menara.

    PERINGATAN: tes ini tidak menjamin angkanya realistis. Dengan antena
    dianggap menyebar rata, daya di bawah menara keluar sekitar -6 dBm,
    sedangkan kenyataannya jauh lebih lemah karena titik itu ada di daerah buta
    antena. Batasan itu diketahui dan dicatat, bukan diperbaiki di sini.
    """
    lon, lat = 117.15, -0.50
    kotak_rapat = BoundingBox(
        min_lon=lon - 0.002, min_lat=lat - 0.002, max_lon=lon + 0.002, max_lat=lat + 0.002
    )
    grid = build_grid(kotak_rapat, resolution_m=50)
    hasil = compute_coverage(grid, satu_pemancar(lon, lat), permukaan_datar())
    puncak = float(np.nanmax(hasil.received_power_dbm))

    miring = EIRP_DBM - float(free_space_loss_db(TINGGI_ANTENA_M - 1.5, FREKUENSI_MHZ))
    mendatar = EIRP_DBM - float(free_space_loss_db(1.0, FREKUENSI_MHZ))

    assert puncak == pytest.approx(miring, abs=1.0)
    assert puncak < mendatar - 20.0


def test_bukit_mengurangi_daya() -> None:
    """Medan berbukit tidak boleh menghasilkan daya yang sama dengan datar."""
    grid = build_grid(KOTAK, resolution_m=2000)
    pemancar = satu_pemancar(117.11, -0.46)

    datar = compute_coverage(grid, pemancar, permukaan_datar())

    data = np.full((200, 200), 0.0, dtype=float)
    data[45:55, 25:35] = 600.0  # punggungan tinggi di tengah kotak
    berbukit = ElevationSurface(
        elevations=data,
        transform=rasterio.Affine(0.005, 0.0, 117.0, 0.0, -0.005, -0.3),
        nodata=None,
        crs="EPSG:4326",
    )
    dengan_bukit = compute_coverage(grid, pemancar, berbukit)

    assert np.nanmin(dengan_bukit.received_power_dbm) < np.nanmin(datar.received_power_dbm)
    assert np.all(dengan_bukit.received_power_dbm <= datar.received_power_dbm + 0.01)


def test_mengambil_terkuat_bukan_menjumlahkan() -> None:
    """Dua pemancar berdampingan tidak boleh menggandakan dayanya.

    Ponsel menempel ke satu sel. Menjumlahkan akan membuat daerah padat menara
    terlihat jauh lebih baik dari kenyataan.
    """
    grid = build_grid(KOTAK, resolution_m=2000)
    satu = compute_coverage(grid, satu_pemancar(117.15, -0.50), permukaan_datar())

    berdua = TransmitterSet(
        lon=np.array([117.15, 117.15]),
        lat=np.array([-0.50, -0.50]),
        operator_id=np.array(["telkomsel"] * 2, dtype=object),
        frequency_mhz=np.array([FREKUENSI_MHZ] * 2),
        antenna_height_m=np.array([TINGGI_ANTENA_M] * 2),
        eirp_dbm=np.array([EIRP_DBM] * 2),
    )
    dua = compute_coverage(grid, berdua, permukaan_datar())

    assert np.allclose(satu.received_power_dbm, dua.received_power_dbm, atol=0.01)


def test_pemancar_jauh_menandai_data_tidak_memadai() -> None:
    """Pemancar terdekat di luar jangkauan berarti wilayahnya tidak terdata.

    Ini yang membedakan 'sinyal lemah' dari 'tidak ada datanya' — FR-011.
    """
    jauh = BoundingBox(min_lon=118.5, min_lat=-1.5, max_lon=118.6, max_lat=-1.4)
    grid = build_grid(jauh, resolution_m=2000)
    hasil = compute_coverage(grid, satu_pemancar(117.15, -0.50), permukaan_datar())
    assert not hasil.data_adequate.any()


def test_dekat_pemancar_dianggap_terdata() -> None:
    grid = build_grid(KOTAK, resolution_m=2000)
    hasil = compute_coverage(grid, satu_pemancar(117.15, -0.50), permukaan_datar())
    assert hasil.data_adequate.any()


def test_ambang_kecukupan_data_masuk_akal() -> None:
    """Lima kilometer, diambil dari jari-jari sel makro pedesaan ITU-R M.2292."""
    assert pytest.approx(5000.0) == DATA_ADEQUATE_RADIUS_M


def test_bentuk_hasil_sama_dengan_kisi() -> None:
    grid = build_grid(KOTAK, resolution_m=2000)
    hasil = compute_coverage(grid, satu_pemancar(117.15, -0.50), permukaan_datar())
    assert hasil.received_power_dbm.shape == grid.shape
    assert hasil.data_adequate.shape == grid.shape

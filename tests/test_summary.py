"""Tes ringkasan per kecamatan.

Yang diuji di sini bukan angkanya cantik, melainkan tiga hal yang kalau salah
akan membuat tabelnya berbohong dengan meyakinkan:

1. sel ditetapkan ke kecamatan lewat poligon, bukan titik tengah terdekat;
2. sel yang datanya tidak memadai tidak ikut menarik angkanya;
3. kecamatan tanpa data sama sekali dilaporkan kosong, bukan nol.
"""

import numpy as np
import pytest

from dapur.constants import BoundingBox
from dapur.grid.build import build_grid
from dapur.propagation.received_power import Coverage
from dapur.tiles.summary import (
    build_summary,
    district_mask,
    summarize_district,
)

# Kotak kecil di sekitar Samarinda; cukup untuk beberapa ratus sel.
KOTAK = BoundingBox(min_lon=117.10, min_lat=-0.52, max_lon=117.14, max_lat=-0.48)


def kisi():
    return build_grid(KOTAK, resolution_m=500)


def persegi(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]
        ],
    }


def cakupan_seragam(bentuk, dbm: float, *, memadai: bool = True) -> Coverage:
    return Coverage(
        received_power_dbm=np.full(bentuk, dbm),
        data_adequate=np.full(bentuk, memadai, dtype=bool),
    )


def test_topeng_memilih_hanya_sel_di_dalam_poligon():
    grid = kisi()
    separuh_barat = persegi(117.10, -0.52, 117.12, -0.48)

    topeng = district_mask(grid, separuh_barat)

    assert topeng.any(), "poligon menutupi separuh kisi, tidak mungkin kosong"
    assert not topeng.all(), "poligon cuma separuh kisi, tidak mungkin penuh"
    assert grid.lon[topeng].max() <= 117.12
    assert grid.lon[~topeng].min() >= 117.12


def test_poligon_menang_atas_titik_tengah_terdekat():
    """Kecamatan panjang tipis di tepi menangkap sel yang titik tengahnya jauh.

    Ini kasus yang membedakan poligon dari 'kecamatan terdekat'. Sel di ujung
    utara jalur ini jauh lebih dekat ke titik tengah kotak besar di sebelahnya,
    tapi ia berada DI DALAM jalur — jadi ia milik jalur itu.
    """
    grid = kisi()
    jalur_tepi = persegi(117.10, -0.52, 117.105, -0.48)

    topeng = district_mask(grid, jalur_tepi)

    titik_tengah_jalur = 117.1025
    titik_tengah_tetangga = 117.125
    lon_terpilih = grid.lon[topeng]
    assert lon_terpilih.size > 0
    # Sel yang terpilih semuanya di dalam jalur, walau sebagian di antaranya
    # lebih dekat ke titik tengah tetangga daripada ke titik tengah jalur.
    assert lon_terpilih.max() <= 117.105
    jarak_ke_jalur = np.abs(lon_terpilih - titik_tengah_jalur)
    jarak_ke_tetangga = np.abs(lon_terpilih - titik_tengah_tetangga)
    assert (jarak_ke_jalur < jarak_ke_tetangga).all()


def test_sel_tidak_memadai_tidak_ikut_menarik_angka():
    """Sel tanpa menara terdaftar tidak boleh menurunkan angka kecamatan.

    Kalau ikut, kecamatan yang datanya bolong akan terbaca sebagai kecamatan
    yang sinyalnya buruk — persis kekeliruan yang dilarang FR-011.
    """
    bentuk = (4, 4)
    daya = np.full(bentuk, -50.0)
    daya[0, :] = -120.0  # baris tanpa menara terdaftar
    memadai = np.ones(bentuk, dtype=bool)
    memadai[0, :] = False
    cakupan = Coverage(received_power_dbm=daya, data_adequate=memadai)

    hasil = summarize_district(cakupan, np.ones(bentuk, dtype=bool))

    assert hasil.dbm_tengah == pytest.approx(-50.0)
    assert hasil.sel == 16, "sel tak terdata tetap dihitung sebagai bagian kecamatan"
    assert hasil.sel_memadai == 12, "tapi tidak ikut jadi bahan angkanya"


def test_kecamatan_tanpa_data_memadai_melaporkan_kosong_bukan_nol():
    bentuk = (3, 3)
    cakupan = cakupan_seragam(bentuk, -95.0, memadai=False)

    hasil = summarize_district(cakupan, np.ones(bentuk, dtype=bool))

    assert hasil.dbm_tengah is None
    assert hasil.dbm_bawah is None
    assert hasil.dbm_atas is None
    assert hasil.sel == 9
    assert hasil.sel_memadai == 0


def test_nan_tidak_bocor_jadi_angka():
    bentuk = (2, 2)
    daya = np.array([[-50.0, np.nan], [-60.0, -70.0]])
    cakupan = Coverage(received_power_dbm=daya, data_adequate=np.ones(bentuk, dtype=bool))

    hasil = summarize_district(cakupan, np.ones(bentuk, dtype=bool))

    assert hasil.dbm_tengah is not None
    assert not np.isnan(hasil.dbm_tengah)
    assert hasil.sel_memadai == 3


def test_rentang_menunjukkan_kecamatan_yang_terbelah():
    """Kecamatan separuh bagus separuh buruk harus terlihat lebar, bukan sedang.

    Kalau cuma angka tengah yang dilaporkan, kecamatan begini terbaca sama
    dengan kecamatan yang merata di angka itu — padahal pengalamannya jauh
    berbeda bagi yang tinggal di separuh yang buruk.
    """
    daya = np.concatenate([np.full(50, -30.0), np.full(50, -90.0)]).reshape(10, 10)
    cakupan = Coverage(received_power_dbm=daya, data_adequate=np.ones((10, 10), dtype=bool))

    hasil = summarize_district(cakupan, np.ones((10, 10), dtype=bool))

    assert hasil.dbm_atas - hasil.dbm_bawah > 50


def test_ringkasan_memuat_semua_operator_dan_terurut():
    grid = kisi()
    bentuk = grid.shape
    kecamatan = {
        "type": "FeatureCollection",
        "features": [
            {"properties": {"nama": "Zulu"}, "geometry": persegi(117.10, -0.52, 117.12, -0.48)},
            {"properties": {"nama": "Alfa"}, "geometry": persegi(117.12, -0.52, 117.14, -0.48)},
        ],
    }
    cakupan = {
        "telkomsel": cakupan_seragam(bentuk, -45.0),
        "ioh": cakupan_seragam(bentuk, -65.0),
    }

    hasil = build_summary(grid, cakupan, kecamatan)

    assert [k["nama"] for k in hasil["kecamatan"]] == ["Alfa", "Zulu"]
    assert hasil["kerincian_m"] == 500
    for k in hasil["kecamatan"]:
        assert set(k["operator"]) == {"telkomsel", "ioh"}
        assert k["operator"]["telkomsel"]["dbm_tengah"] == pytest.approx(-45.0)
        assert k["operator"]["ioh"]["dbm_tengah"] == pytest.approx(-65.0)


def test_kecamatan_di_luar_kisi_dibuang():
    grid = kisi()
    kecamatan = {
        "type": "FeatureCollection",
        "features": [
            {"properties": {"nama": "Di dalam"}, "geometry": persegi(117.10, -0.52, 117.14, -0.48)},
            {"properties": {"nama": "Jauh"}, "geometry": persegi(118.0, -1.0, 118.1, -0.9)},
        ],
    }
    cakupan = {"telkomsel": cakupan_seragam(grid.shape, -45.0)}

    hasil = build_summary(grid, cakupan, kecamatan)

    assert [k["nama"] for k in hasil["kecamatan"]] == ["Di dalam"]

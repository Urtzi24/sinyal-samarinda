"""Tes kemampuan melanjutkan — Prinsip IV.

Menghitung seluruh Samarinda pada kerincian 30 m makan lebih dari satu jam.
Kalau listrik padam di menit ke-50, dapur harus melanjutkan dari yang sudah
jadi, bukan mengulang dari nol. Yang diuji di sini justru hal yang tidak
kelihatan dari keluaran layar: bahwa pekerjaan yang dilewati benar-benar tidak
dikerjakan, bukan dikerjakan ulang lalu ditimpa dengan hasil yang sama.

Karena itu tesnya menghitung berapa kali mesin hitungnya dipanggil, bukan
memeriksa berkasnya ada. Berkas yang ada tidak membuktikan apa pun soal apakah
waktunya terbuang.
"""

import numpy as np
import pytest

from dapur import run
from dapur.propagation.received_power import Coverage
from dapur.sources.fetch import skip_if_exists
from dapur.sources.transmitters import TransmitterSet

# Kerincian sengaja kasar: yang diuji logika melewati pekerjaan, bukan fisikanya.
# Kisi 5 km membuat tesnya selesai dalam sekejap.
KERINCIAN_UJI = 5000.0

OPERATOR_UJI = ["ioh", "telkomsel", "xlsmart"]


class PemanggilanTercatat:
    """Pengganti mesin hitung yang mencatat operator mana saja yang dihitung."""

    def __init__(self) -> None:
        self.dipanggil: list[int] = []

    def __call__(self, grid, tx, surface) -> Coverage:
        self.dipanggil.append(len(tx))
        return Coverage(
            received_power_dbm=np.full(grid.shape, -50.0),
            data_adequate=np.ones(grid.shape, dtype=bool),
        )


def pemancar_palsu() -> TransmitterSet:
    """Satu pemancar per operator, di tengah Samarinda."""
    return TransmitterSet(
        lon=np.array([117.15, 117.16, 117.17]),
        lat=np.array([-0.50, -0.51, -0.52]),
        operator_id=np.array(OPERATOR_UJI),
        frequency_mhz=np.array([1800.0, 900.0, 1800.0]),
        antenna_height_m=np.array([25.0, 30.0, 25.0]),
        eirp_dbm=np.array([59.0, 58.0, 59.0]),
    )


@pytest.fixture
def dapur_terisolasi(tmp_path, monkeypatch):
    """Arahkan dapur ke folder sementara, dan ganti mesin hitungnya.

    Yang ditukar cuma yang menyentuh cakram dan yang mahal. Logika melanjutkan
    sendiri — bagian yang sedang diuji — tetap yang asli.
    """
    monkeypatch.setattr(run, "INTERMEDIATE_DIR", tmp_path / "antara")
    monkeypatch.setattr(run, "load_transmitters", pemancar_palsu)
    dem_palsu = type("DemPalsu", (), {"load": staticmethod(lambda p: None)})
    monkeypatch.setattr(run, "ElevationSurface", dem_palsu)

    dem = tmp_path / f"{run.DEM_TILE_NAME}.tif"
    dem.write_bytes(b"bukan GeoTIFF sungguhan; cuma harus ada")
    monkeypatch.setattr(run, "RAW_DIR", tmp_path)

    mesin = PemanggilanTercatat()
    monkeypatch.setattr(run, "compute_coverage", mesin)
    return mesin


def hitung(operators: list[str], *, force: bool = False) -> None:
    run.step_compute(resolution_m=KERINCIAN_UJI, operators=operators, force=force)


def test_jalan_kedua_tidak_menghitung_apa_pun_lagi(dapur_terisolasi):
    hitung(OPERATOR_UJI)
    assert len(dapur_terisolasi.dipanggil) == 3

    dapur_terisolasi.dipanggil.clear()
    hitung(OPERATOR_UJI)

    assert dapur_terisolasi.dipanggil == [], "yang sudah ada tidak boleh dihitung ulang"


def test_berhenti_di_tengah_lalu_lanjut_hanya_mengerjakan_sisanya(dapur_terisolasi):
    """Kasus yang sebenarnya: mati listrik setelah dua operator selesai."""
    hitung(OPERATOR_UJI[:2])
    assert len(dapur_terisolasi.dipanggil) == 2

    dapur_terisolasi.dipanggil.clear()
    hitung(OPERATOR_UJI)

    assert len(dapur_terisolasi.dipanggil) == 1, "cuma operator ketiga yang tersisa"


def test_hasil_yang_sudah_ada_tidak_ikut_berubah(dapur_terisolasi):
    """Melewati harus benar-benar melewati, bukan menulis ulang isi yang sama.

    Kalau berkasnya ditimpa, berkas yang setengah tertulis saat listrik padam
    akan tetap rusak setelah dijalankan ulang — dan itu justru keadaan yang
    kemampuan melanjutkan ini seharusnya selamatkan.
    """
    hitung(OPERATOR_UJI)
    jalur = run._grid_path(OPERATOR_UJI[0], KERINCIAN_UJI)
    sebelum = jalur.stat().st_mtime_ns

    hitung(OPERATOR_UJI)

    assert jalur.stat().st_mtime_ns == sebelum


def test_paksa_ulang_mengabaikan_yang_sudah_ada(dapur_terisolasi):
    hitung(OPERATOR_UJI)
    dapur_terisolasi.dipanggil.clear()

    hitung(OPERATOR_UJI, force=True)

    assert len(dapur_terisolasi.dipanggil) == 3


def test_kerincian_berbeda_dihitung_sendiri(dapur_terisolasi):
    """Hasil 5 km tidak boleh dianggap mewakili hasil 10 km.

    Nama berkasnya memuat kerinciannya justru untuk ini. Kalau tidak, menaikkan
    kerincian akan diam-diam memakai hasil lama yang lebih kasar.
    """
    hitung(OPERATOR_UJI)
    dapur_terisolasi.dipanggil.clear()

    run.step_compute(resolution_m=10000.0, operators=OPERATOR_UJI, force=False)

    assert len(dapur_terisolasi.dipanggil) == 3


def test_skip_if_exists_hanya_melewati_yang_benar_benar_ada(tmp_path):
    target = tmp_path / "belum" / "ada.txt"

    assert skip_if_exists(target, "uji", force=False) is False
    assert target.parent.is_dir(), "folder induknya disiapkan sekalian"

    target.write_text("ada")
    assert skip_if_exists(target, "uji", force=False) is True
    assert skip_if_exists(target, "uji", force=True) is False

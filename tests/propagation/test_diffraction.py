"""Tes angka acuan difraksi mata pisau tunggal.

Sumber: Recommendation ITU-R P.526-14 (01/2018), "Propagation by diffraction",
bagian 4.1. Diambil dari itu.int, 14 Agustus 2026.

    pers. (26)  nu = h * sqrt( (2/lambda) * (1/d1 + 1/d2) )
                h  : tinggi puncak penghalang di atas garis lurus penghubung
                     kedua ujung lintasan; negatif kalau di bawah garis itu
                d1, d2 : jarak kedua ujung lintasan ke puncak penghalang
                satuan harus saling konsisten

    pers. (31)  J(nu) = 6,9 + 20 log10( sqrt((nu - 0,1)^2 + 1) + nu - 0,1 )  dB
                berlaku untuk nu > -0,78

Jujur soal sifat tiap angka di bawah, karena ini yang membedakan tes acuan dari
tes yang menguji rumus terhadap dirinya sendiri:

  - **J(0) ≈ 6 dB** dan **J(-0,78) ≈ 0 dB** adalah jangkar yang berdiri sendiri.
    Yang pertama nilai klasik saat penghalang tepat menyerempet garis pandang.
    Yang kedua adalah batas keberlakuan yang disebut rekomendasinya sendiri —
    dan rumusnya memang meluruh ke nol persis di sana. Kalau salah satu meleset,
    rumusnya salah bentuk, bukan cuma salah angka.
  - **J(1), J(2), J(3)** dihitung dari pers. (31) dan berfungsi sebagai kunci
    regresi, bukan bukti berdiri sendiri. Nilainya juga bisa dicocokkan dengan
    Gambar 9 di rekomendasi yang sama, yang sumbunya berjalan dari nu -3 sampai
    3 dan J -2 sampai 24 dB.
"""

import numpy as np
import pytest

from dapur.propagation.diffraction import (
    deygout_loss_db,
    fresnel_kirchoff_parameter,
    knife_edge_loss_db,
)

# Sekitar 1 800 MHz — pita LTE yang diasumsikan di dapur/constants.py.
LAMBDA_M = 0.1666

TOLERANSI_DB = 0.01

# Batas keberlakuan pers. (31), disebut langsung di teks rekomendasi.
NU_BATAS_BERLAKU = -0.78


def test_serempet_garis_pandang_sekitar_6_db() -> None:
    """nu = 0 berarti penghalang tepat menyentuh garis pandang.

    Nilai 6 dB di titik ini adalah hasil klasik difraksi mata pisau: separuh
    muka gelombang tertutup, dayanya turun seperempat. Kalau tes ini gagal,
    bentuk rumusnya salah — bukan sekadar tetapannya bergeser.
    """
    assert knife_edge_loss_db(0.0) == pytest.approx(6.03, abs=0.05)


def test_meluruh_ke_nol_di_batas_keberlakuan() -> None:
    """Pers. (31) berlaku untuk nu > -0,78, dan memang meluruh ke 0 dB di sana.

    Ini bukan kebetulan: batas itu dipilih justru karena di bawahnya rumus
    pendekatannya berhenti masuk akal. Kalau nilai di sini bukan sekitar nol,
    tanda kurung di dalam logaritma kemungkinan tertukar.
    """
    assert knife_edge_loss_db(NU_BATAS_BERLAKU) == pytest.approx(0.0, abs=0.05)


@pytest.mark.parametrize(
    ("nu", "loss_db"),
    [
        (1.0, 13.92),
        (2.0, 19.04),
        (3.0, 22.42),
    ],
)
def test_kunci_regresi_pers_31(nu: float, loss_db: float) -> None:
    """Nilai dari pers. (31), dicocokkan juga dengan Gambar 9 di rekomendasi."""
    assert knife_edge_loss_db(nu) == pytest.approx(loss_db, abs=0.05)


def test_tanpa_penghalang_tidak_menambah_redaman() -> None:
    """Di bawah batas keberlakuan, redamannya nol — bukan negatif.

    Redaman negatif berarti sinyal menguat karena ada bukit, dan peta yang
    menampilkan itu akan terlihat masuk akal sambil salah sepenuhnya.
    """
    for nu in (-1.0, -2.0, -5.0):
        assert knife_edge_loss_db(nu) == 0.0


def test_redaman_naik_bersama_nu() -> None:
    """Makin dalam penghalang menutup lintasan, makin besar redamannya.

    Invarian arah seperti ini menangkap tanda yang terbalik — jenis kesalahan
    yang tidak terlihat dari satu titik uji mana pun.
    """
    nu = np.linspace(NU_BATAS_BERLAKU, 5.0, 50)
    rugi = knife_edge_loss_db(nu)
    assert np.all(np.diff(rugi) > 0)


def test_menerima_larik_numpy() -> None:
    """Dihitung untuk jutaan pasangan pemancar-sel sekaligus."""
    nu = np.array([0.0, 1.0, 2.0])
    hasil = knife_edge_loss_db(nu)
    assert isinstance(hasil, np.ndarray)
    assert hasil.shape == nu.shape
    assert hasil == pytest.approx([6.03, 13.92, 19.04], abs=0.05)


def test_parameter_nu_nol_saat_penghalang_tepat_di_garis() -> None:
    """h = 0 berarti puncak penghalang persis di garis pandang, jadi nu = 0."""
    nu = fresnel_kirchoff_parameter(
        obstacle_height_m=0.0,
        d1_m=1000.0,
        d2_m=1000.0,
        wavelength_m=0.333,
    )
    assert nu == pytest.approx(0.0, abs=TOLERANSI_DB)


def test_parameter_nu_negatif_saat_penghalang_di_bawah_garis() -> None:
    """Rekomendasi menyatakan h negatif kalau puncaknya di bawah garis pandang.

    Tanda ini menentukan segalanya: h positif berarti lintasan terhalang, h
    negatif berarti lapang. Tertukar, dan peta akan menandai lembah sebagai
    daerah terhalang sekaligus bukit sebagai daerah lapang.
    """
    lapang = fresnel_kirchoff_parameter(
        obstacle_height_m=-50.0, d1_m=2000.0, d2_m=3000.0, wavelength_m=0.333
    )
    terhalang = fresnel_kirchoff_parameter(
        obstacle_height_m=50.0, d1_m=2000.0, d2_m=3000.0, wavelength_m=0.333
    )
    assert lapang < 0 < terhalang
    assert lapang == pytest.approx(-terhalang, abs=TOLERANSI_DB)


def test_parameter_nu_sesuai_bentuk_praktis_rekomendasi() -> None:
    """Pers. (33) menulis ulang pers. (26) dalam satuan praktis.

        nu = 0,0316 * h * sqrt( 2 (d1 + d2) / (lambda d1 d2) )

    dengan h dan lambda dalam meter, d1 dan d2 dalam KILOMETER. Sama seperti tes
    ruang bebas, ini dua bentuk terbitan yang berbeda saling memeriksa.
    """
    h_m = 40.0
    d1_km, d2_km = 3.0, 7.0
    lambda_m = 0.1666  # sekitar 1 800 MHz

    acuan = 0.0316 * h_m * np.sqrt(2 * (d1_km + d2_km) / (lambda_m * d1_km * d2_km))
    hasil = fresnel_kirchoff_parameter(
        obstacle_height_m=h_m,
        d1_m=d1_km * 1000,
        d2_m=d2_km * 1000,
        wavelength_m=lambda_m,
    )
    assert hasil == pytest.approx(acuan, rel=0.01)


# ---------------------------------------------------------------------------
# Penggabungan Deygout untuk lintasan dengan beberapa penghalang
# ---------------------------------------------------------------------------
#
# Deygout adalah konstruksi, bukan rumus dengan nilai terbitan. Jadi yang diuji
# di sini invariannya — hal yang wajib benar apa pun angkanya. Redaman tiap
# penghalang tunggalnya tetap memakai pers. (31), yang sudah diuji di atas.


def test_medan_datar_tidak_meredam() -> None:
    """Tanah datar dengan antena di atasnya berarti lintasan lapang.

    Tes ini menangkap kesalahan nyata saat pertama dijalankan: tanpa syarat
    bahwa penghalang harus berupa puncak, lintasan datar sepanjang 10 km
    menghasilkan 15,4 dB redaman. Sebabnya tanah di dekat penerima setinggi
    1,5 m memang masuk ke zona Fresnel, sehingga tiap titik cuplik terbaca
    sebagai mata pisau.

    Angka semacam itu terlihat masuk akal, jadi tidak ada yang akan curiga —
    persis alasan Prinsip I ada.
    """
    jarak = np.linspace(0, 10_000, 50)
    tinggi = np.zeros_like(jarak)
    rugi = deygout_loss_db(jarak, tinggi, tx_height_m=30, rx_height_m=1.5, wavelength_m=LAMBDA_M)
    assert rugi == 0.0


def test_satu_bukit_sama_dengan_mata_pisau_tunggal() -> None:
    """Profil tiga titik cuma punya satu penghalang, jadi Deygout menyusut.

    Ini penghubung antara konstruksi Deygout dan rumus terbitan ITU: dengan satu
    penghalang, hasilnya wajib persis sama dengan pers. (31). Kalau berbeda, ada
    kesalahan di penarikan garis pandang atau di pembagian lintasan.
    """
    jarak = np.array([0.0, 5000.0, 10_000.0])
    tinggi = np.array([0.0, 200.0, 0.0])
    tx_h, rx_h = 30.0, 1.5

    # Garis pandang dari puncak antena pemancar ke puncak antena penerima.
    garis_di_tengah = tx_h + (rx_h - tx_h) * 0.5
    h = 200.0 - garis_di_tengah
    nu = fresnel_kirchoff_parameter(
        obstacle_height_m=h, d1_m=5000.0, d2_m=5000.0, wavelength_m=LAMBDA_M
    )

    rugi = deygout_loss_db(jarak, tinggi, tx_height_m=tx_h, rx_height_m=rx_h, wavelength_m=LAMBDA_M)
    assert rugi == pytest.approx(knife_edge_loss_db(nu), abs=0.01)


def test_bukit_lebih_tinggi_lebih_meredam() -> None:
    """Arah yang wajib benar: makin tinggi penghalang, makin besar redamannya."""
    jarak = np.array([0.0, 5000.0, 10_000.0])
    rugi = [
        deygout_loss_db(
            jarak,
            np.array([0.0, h, 0.0]),
            tx_height_m=30,
            rx_height_m=1.5,
            wavelength_m=LAMBDA_M,
        )
        for h in (50.0, 100.0, 200.0, 400.0)
    ]
    assert rugi == sorted(rugi)
    assert rugi[0] > 0


def test_dua_bukit_meredam_lebih_dari_satu() -> None:
    """Inti Deygout: penghalang di luar yang utama tetap menyumbang redaman.

    Kalau dua bukit menghasilkan angka yang sama dengan satu bukit, penelusuran
    ke potongan lintasan tidak berjalan — dan metodenya menyusut kembali jadi
    mata pisau tunggal tanpa ada yang menyadarinya.
    """
    jarak = np.array([0.0, 2500.0, 5000.0, 7500.0, 10_000.0])
    satu = deygout_loss_db(
        jarak,
        np.array([0.0, 0.0, 200.0, 0.0, 0.0]),
        tx_height_m=30,
        rx_height_m=1.5,
        wavelength_m=LAMBDA_M,
    )
    dua = deygout_loss_db(
        jarak,
        np.array([0.0, 150.0, 200.0, 0.0, 0.0]),
        tx_height_m=30,
        rx_height_m=1.5,
        wavelength_m=LAMBDA_M,
    )
    assert dua > satu


def test_profil_terlalu_pendek_tidak_meledak() -> None:
    """Dua titik berarti tidak ada apa pun di antara kedua ujung.

    Sel yang sangat dekat dengan menara menghasilkan profil sependek ini. Ia
    harus mengembalikan nol, bukan melempar galat yang menghentikan seluruh
    perhitungan kota.
    """
    jarak = np.array([0.0, 30.0])
    tinggi = np.array([10.0, 12.0])
    rugi = deygout_loss_db(jarak, tinggi, tx_height_m=30, rx_height_m=1.5, wavelength_m=LAMBDA_M)
    assert rugi == 0.0

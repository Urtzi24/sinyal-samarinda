"""Tes ketaatan konstanta pada dirinya sendiri.

Bukan tes fisika — itu ada di tests/propagation/. Ini menjaga hal-hal yang
gampang melenceng diam-diam saat konstanta ditambah nanti.
"""

from dapur.constants import (
    MNC_TO_OPERATOR,
    OPENCELLID_COLUMNS,
    OPERATOR_DISPLAY_NAMES,
    RADIO_ASSUMPTIONS,
    SAMARINDA_BBOX,
)


def test_tiap_operator_punya_nama_tampil() -> None:
    """Menambah MNC baru tanpa nama tampilnya akan menghasilkan tombol kosong.

    Peta yang menampilkan tombol tanpa nama tidak bisa dipakai membandingkan
    operator, dan itu inti kegunaannya.
    """
    operator_ids = set(MNC_TO_OPERATOR.values())
    assert operator_ids == set(OPERATOR_DISPLAY_NAMES)


def test_tiga_operator_pada_2026() -> None:
    """Lima kode MNC di data terbuka, tiga operator setelah dua penggabungan.

    Kalau tes ini gagal, kemungkinan ada penggabungan baru — perbarui
    docs/LANGKAH-0.md dan PRD bagian 14 sekalian, jangan cuma tesnya.
    """
    assert set(MNC_TO_OPERATOR.values()) == {"telkomsel", "ioh", "xlsmart"}


def test_kotak_batas_tidak_terbalik() -> None:
    """Samarinda ada di selatan khatulistiwa, jadi lintangnya negatif.

    Kotak batas yang terbalik tidak menghasilkan galat — ia menghasilkan kisi
    kosong, dan kisi kosong terbaca seperti kota tanpa sinyal.
    """
    assert SAMARINDA_BBOX.min_lon < SAMARINDA_BBOX.max_lon
    assert SAMARINDA_BBOX.min_lat < SAMARINDA_BBOX.max_lat
    assert SAMARINDA_BBOX.max_lat < 0


def test_asumsi_pemancar_menutup_semua_jenis_radio() -> None:
    """Jenis radio tanpa asumsi akan membuat selnya terlewat diam-diam.

    Sel yang terlewat tidak menghasilkan galat — ia menghasilkan daerah yang
    terlihat lebih buruk dari kenyataan, dan itu tidak terlihat oleh siapa pun.
    """
    assert set(RADIO_ASSUMPTIONS) == {"GSM", "UMTS", "LTE"}


def test_tinggi_antena_turun_saat_frekuensi_naik() -> None:
    """Pola dari ITU-R M.2292: makin tinggi pita, makin rendah antena makro.

    30 m di bawah 1 GHz, 25 m di 1-2 GHz, 20 m di 2-3 GHz. Kalau urutan ini
    terbalik, kemungkinan ada angka yang tertukar antar baris tabel.
    """
    urut = sorted(RADIO_ASSUMPTIONS.values(), key=lambda a: a.frequency_mhz)
    tinggi = [a.antenna_height_m for a in urut]
    assert tinggi == sorted(tinggi, reverse=True)


def test_nama_kolom_opencellid_sesuai_urutan_berkas() -> None:
    """Kolom lon dan lat mudah tertukar, dan tertukarnya tidak menghasilkan galat.

    Samarinda ada di 117 BT, 0,5 LS. Kalau lon dan lat tertukar, seluruh kota
    pindah ke tengah Samudra Hindia dan kisinya kosong tanpa satu pun peringatan.
    """
    assert OPENCELLID_COLUMNS.index("lon") == 6
    assert OPENCELLID_COLUMNS.index("lat") == 7
    assert OPENCELLID_COLUMNS.index("radio") == 0
    assert OPENCELLID_COLUMNS.index("net") == 2

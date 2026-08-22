"""Tes penyaring pemancar.

Aturan sahnya ada di specs/001-signal-prediction-map/data-model.md, entitas
Transmitter. Tiap aturan diuji sendiri-sendiri: penyaring yang membuang terlalu
banyak menghasilkan peta kosong, dan penyaring yang membuang terlalu sedikit
menghasilkan peta yang salah. Dua-duanya tidak melempar galat.
"""

import csv
import gzip
from pathlib import Path

import pytest

from dapur.constants import OPENCELLID_COLUMNS, SAMARINDA_BBOX
from dapur.sources.transmitters import expand_bounding_box, filter_transmitters

# Satu titik di tengah Samarinda.
LON_TENGAH = 117.15
LAT_TENGAH = -0.5


def baris(
    radio: str = "LTE",
    mcc: int = 510,
    net: int = 10,
    lon: float = LON_TENGAH,
    lat: float = LAT_TENGAH,
    samples: int = 5,
) -> list[str]:
    """Satu baris OpenCelliD yang sah, dengan bagian yang perlu diubah saja."""
    nilai = {
        "radio": radio,
        "mcc": mcc,
        "net": net,
        "area": 1,
        "cell": 1,
        "unit": "",
        "lon": lon,
        "lat": lat,
        "range": 1000,
        "samples": samples,
        "changeable": 1,
        "created": 0,
        "updated": 0,
        "averageSignal": -80,
    }
    return [str(nilai[k]) for k in OPENCELLID_COLUMNS]


def tulis_csv(tmp_path: Path, baris_baris: list[list[str]], *, kepala: tuple | None = None) -> Path:
    berkas = tmp_path / "cells.csv.gz"
    with gzip.open(berkas, "wt", encoding="utf-8", newline="") as keluar:
        penulis = csv.writer(keluar)
        penulis.writerow(kepala if kepala is not None else OPENCELLID_COLUMNS)
        penulis.writerows(baris_baris)
    return berkas


def test_baris_sah_lolos(tmp_path: Path) -> None:
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris()]))
    assert len(hasil.transmitters) == 1
    assert hasil.transmitters.operator_id[0] == "telkomsel"


def test_membuang_negara_lain(tmp_path: Path) -> None:
    """MCC selain 510 bukan Indonesia."""
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(mcc=262)]))
    assert len(hasil.transmitters) == 0
    assert hasil.rejected["bukan Indonesia"] == 1


def test_membuang_yang_jauh_di_luar_wilayah(tmp_path: Path) -> None:
    """Jakarta jauh di luar kotak Samarinda walau sudah dilebarkan."""
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(lon=106.8, lat=-6.2)]))
    assert len(hasil.transmitters) == 0
    assert hasil.rejected["di luar wilayah"] == 1


def test_menyimpan_pemancar_tepat_di_luar_batas_kota(tmp_path: Path) -> None:
    """Pemancar di luar batas administratif tetap menyinari kota.

    Kalau baris ini terbuang, pinggiran kota akan terlihat lebih buruk dari
    kenyataan — bukan karena sinyalnya lemah, tapi karena sumbernya dibuang.
    """
    tepat_di_luar = SAMARINDA_BBOX.max_lat + 0.05  # sekitar 5 km di utara batas
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(lat=tepat_di_luar)]))
    assert len(hasil.transmitters) == 1


def test_membuang_tanpa_cuplikan(tmp_path: Path) -> None:
    """Perkiraan posisi tanpa satu pun pengukuran tidak punya dasar."""
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(samples=0)]))
    assert len(hasil.transmitters) == 0
    assert hasil.rejected["tanpa cuplikan"] == 1


def test_membuang_operator_tak_dikenal_dengan_menyebut_kodenya(tmp_path: Path) -> None:
    """MNC yang tidak ada di tabel dicatat, bukan diam-diam dianggap terdekat.

    Kode MNC-nya ikut ditulis di alasan pembuangan. Tanpa itu, munculnya
    operator baru cuma terlihat sebagai angka yang naik tanpa keterangan.
    """
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(net=99)]))
    assert len(hasil.transmitters) == 0
    assert hasil.rejected["operator tak dikenal (MNC 99)"] == 1


def test_membuang_jenis_radio_tak_dikenal(tmp_path: Path) -> None:
    """NR (5G) belum punya asumsi pemancar, jadi dibuang terang-terangan."""
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(radio="NR")]))
    assert len(hasil.transmitters) == 0
    assert hasil.rejected["radio tak dikenal (NR)"] == 1


def test_menggabungkan_mnc_lama_jadi_tiga_operator(tmp_path: Path) -> None:
    """Lima kode MNC, tiga operator — dua penggabungan sudah terjadi."""
    hasil = filter_transmitters(
        tulis_csv(
            tmp_path,
            [
                baris(net=10),  # Telkomsel
                baris(net=1),  # Indosat lama
                baris(net=89),  # Tri lama
                baris(net=11),  # XL lama
                baris(net=28),  # Smartfren lama
            ],
        )
    )
    assert hasil.per_operator["telkomsel"] == 1
    assert hasil.per_operator["ioh"] == 2
    assert hasil.per_operator["xlsmart"] == 2


def test_asumsi_pemancar_menempel_per_jenis_radio(tmp_path: Path) -> None:
    """Frekuensi, tinggi antena, dan EIRP ikut dari jenis radionya."""
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(radio="GSM"), baris(radio="UMTS")]))
    assert list(hasil.transmitters.frequency_mhz) == [900, 2100]
    assert list(hasil.transmitters.antenna_height_m) == [30, 20]


def test_kepala_berkas_salah_ditolak_terang_terangan(tmp_path: Path) -> None:
    """Urutan kolom yang berubah harus menghentikan dapur, bukan diam-diam salah.

    Kalau lon dan lat tertukar dan berkasnya tetap dibaca, seluruh Samarinda
    pindah ke tengah Samudra Hindia dan kisinya kosong tanpa satu pun peringatan.
    """
    kepala_salah = ("radio", "mcc", "net", "lat", "lon")
    with pytest.raises(ValueError, match="kepala berkas"):
        filter_transmitters(tulis_csv(tmp_path, [], kepala=kepala_salah))


def test_memilih_bagian_satu_operator(tmp_path: Path) -> None:
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(net=10), baris(net=11), baris(net=10)]))
    telkomsel = hasil.transmitters.for_operator("telkomsel")
    assert len(telkomsel) == 2
    assert set(telkomsel.operator_id) == {"telkomsel"}


def test_pelebaran_kotak_menambah_ke_segala_arah() -> None:
    luas = expand_bounding_box(SAMARINDA_BBOX, 20_000)
    assert luas.min_lon < SAMARINDA_BBOX.min_lon
    assert luas.max_lon > SAMARINDA_BBOX.max_lon
    assert luas.min_lat < SAMARINDA_BBOX.min_lat
    assert luas.max_lat > SAMARINDA_BBOX.max_lat


def test_ringkasan_menyebut_angka_bukan_cuma_selesai(tmp_path: Path) -> None:
    """dapur-cli.md mewajibkan tiap langkah melaporkan angka, bukan 'selesai'."""
    hasil = filter_transmitters(tulis_csv(tmp_path, [baris(), baris(mcc=262), baris(samples=0)]))
    teks = hasil.summary()
    assert "dibaca" in teks
    assert "bukan Indonesia" in teks
    assert "tanpa cuplikan" in teks

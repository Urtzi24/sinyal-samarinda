"""Penyaring baris OpenCelliD jadi daftar pemancar Samarinda.

Membaca berkas, tidak menyentuh jaringan.

Berkas sumbernya besar — 707 MB terkompresi, sekitar 3,3 GB setelah dibuka — jadi
dibaca mengalir baris per baris, tidak dimuat sekaligus ke memori.

Aturan sah yang ditegakkan di sini ada di
specs/001-signal-prediction-map/data-model.md, entitas Transmitter.
"""

import csv
import gzip
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from dapur.constants import (
    INDONESIA_MCC,
    METERS_PER_DEGREE_LATITUDE,
    MNC_TO_OPERATOR,
    OPENCELLID_COLUMNS,
    RADIO_ASSUMPTIONS,
    SAMARINDA_BBOX,
    TRANSMITTER_SEARCH_BUFFER_M,
    BoundingBox,
)

COL_RADIO = OPENCELLID_COLUMNS.index("radio")
COL_MCC = OPENCELLID_COLUMNS.index("mcc")
COL_NET = OPENCELLID_COLUMNS.index("net")
COL_LON = OPENCELLID_COLUMNS.index("lon")
COL_LAT = OPENCELLID_COLUMNS.index("lat")
COL_SAMPLES = OPENCELLID_COLUMNS.index("samples")

COLUMN_COUNT = len(OPENCELLID_COLUMNS)


@dataclass(frozen=True)
class TransmitterSet:
    """Daftar pemancar sebagai larik sejajar, siap dihitung sekaligus.

    Bentuk larik dipilih, bukan daftar objek: jutaan pasangan pemancar-sel
    dihitung dengan NumPy, dan daftar objek akan memaksa perulangan Python.
    """

    lon: np.ndarray
    lat: np.ndarray
    operator_id: np.ndarray
    frequency_mhz: np.ndarray
    antenna_height_m: np.ndarray
    eirp_dbm: np.ndarray

    def __len__(self) -> int:
        return int(self.lon.size)

    def for_operator(self, operator_id: str) -> "TransmitterSet":
        """Bagian daftar yang milik satu operator."""
        keep = self.operator_id == operator_id
        return TransmitterSet(
            lon=self.lon[keep],
            lat=self.lat[keep],
            operator_id=self.operator_id[keep],
            frequency_mhz=self.frequency_mhz[keep],
            antenna_height_m=self.antenna_height_m[keep],
            eirp_dbm=self.eirp_dbm[keep],
        )


def _empty_transmitter_set() -> TransmitterSet:
    kosong = np.array([])
    return TransmitterSet(kosong, kosong, kosong, kosong, kosong, kosong)


@dataclass
class FilterResult:
    """Pemancar yang lolos, beserta catatan apa yang dibuang dan kenapa."""

    transmitters: TransmitterSet = field(default_factory=_empty_transmitter_set)
    rows_read: int = 0
    rejected: Counter = field(default_factory=Counter)
    per_operator: Counter = field(default_factory=Counter)

    def summary(self) -> str:
        """Laporan berangka untuk ditampilkan di layar — lihat dapur-cli.md."""
        total = len(self.transmitters)
        lines = [f"  dibaca      : {self.rows_read:,} baris"]
        lines.append(f"  lolos       : {total:,} pemancar")
        for operator, count in self.per_operator.most_common():
            share = count / max(total, 1) * 100
            lines.append(f"      {operator:<12} {count:>7,}  ({share:4.1f}%)")
        lines.append("  dibuang     :")
        for reason, count in self.rejected.most_common():
            lines.append(f"      {reason:<28} {count:>9,}")
        return "\n".join(lines)


def expand_bounding_box(box: BoundingBox, buffer_m: float) -> BoundingBox:
    """Lebarkan kotak batas ke segala arah sejauh `buffer_m`.

    Pemancar di luar batas administratif tetap menyinari kota. Memotong tepat di
    batas kota akan membuat pinggiran kota terlihat lebih buruk dari kenyataan —
    bukan karena sinyalnya lemah, tapi karena sumbernya dibuang.
    """
    d_lat = buffer_m / METERS_PER_DEGREE_LATITUDE
    mid_lat = math.radians((box.min_lat + box.max_lat) / 2)
    d_lon = buffer_m / (METERS_PER_DEGREE_LATITUDE * math.cos(mid_lat))
    return BoundingBox(
        min_lon=box.min_lon - d_lon,
        min_lat=box.min_lat - d_lat,
        max_lon=box.max_lon + d_lon,
        max_lat=box.max_lat + d_lat,
    )


def filter_transmitters(
    csv_gz: Path,
    *,
    box: BoundingBox = SAMARINDA_BBOX,
    buffer_m: float = TRANSMITTER_SEARCH_BUFFER_M,
) -> FilterResult:
    """Baca berkas OpenCelliD, kembalikan pemancar Samarinda saja.

    Args:
        csv_gz: berkas `cell_towers.csv.gz`.
        box: kotak batas kota.
        buffer_m: pelebaran kotak, meter.

    Raises:
        ValueError: kalau kepala berkasnya tidak sesuai dugaan.

    Baris yang dibuang dihitung per golongan alasannya. Angka itu bukan hiasan:
    kalau hampir semua baris terbuang, kemungkinan pemetaan MNC-nya salah — dan
    tanpa laporan per golongan, kesalahan itu cuma terlihat sebagai peta kosong.
    """
    wide = expand_bounding_box(box, buffer_m)

    lons: list[float] = []
    lats: list[float] = []
    operators: list[str] = []
    frequencies: list[float] = []
    heights: list[float] = []
    eirps: list[float] = []

    result = FilterResult()

    with gzip.open(csv_gz, "rt", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != OPENCELLID_COLUMNS:
            raise ValueError(
                f"kepala berkas tidak sesuai dugaan.\n"
                f"  diharapkan: {OPENCELLID_COLUMNS}\n"
                f"  ditemukan : {tuple(header) if header else '(kosong)'}"
            )

        for row in reader:
            result.rows_read += 1

            if len(row) < COLUMN_COUNT:
                result.rejected["baris rusak"] += 1
                continue

            try:
                mcc = int(row[COL_MCC])
                net = int(row[COL_NET])
                lon = float(row[COL_LON])
                lat = float(row[COL_LAT])
                samples = int(row[COL_SAMPLES] or 0)
            except ValueError:
                result.rejected["angka tidak terbaca"] += 1
                continue

            if mcc != INDONESIA_MCC:
                result.rejected["bukan Indonesia"] += 1
                continue

            if not (wide.min_lon <= lon <= wide.max_lon and wide.min_lat <= lat <= wide.max_lat):
                result.rejected["di luar wilayah"] += 1
                continue

            if samples <= 0:
                result.rejected["tanpa cuplikan"] += 1
                continue

            operator = MNC_TO_OPERATOR.get(net)
            if operator is None:
                result.rejected[f"operator tak dikenal (MNC {net})"] += 1
                continue

            assumptions = RADIO_ASSUMPTIONS.get(row[COL_RADIO].strip().upper())
            if assumptions is None:
                result.rejected[f"radio tak dikenal ({row[COL_RADIO]})"] += 1
                continue

            lons.append(lon)
            lats.append(lat)
            operators.append(operator)
            frequencies.append(assumptions.frequency_mhz)
            heights.append(assumptions.antenna_height_m)
            eirps.append(assumptions.eirp_dbm)
            result.per_operator[operator] += 1

    result.transmitters = TransmitterSet(
        lon=np.array(lons, dtype=float),
        lat=np.array(lats, dtype=float),
        operator_id=np.array(operators, dtype=object),
        frequency_mhz=np.array(frequencies, dtype=float),
        antenna_height_m=np.array(heights, dtype=float),
        eirp_dbm=np.array(eirps, dtype=float),
    )
    return result

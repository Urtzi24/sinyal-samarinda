"""Perintah dapur.

Dijalankan dengan tangan, sesekali, saat data diperbarui. Bukan layanan, dan
tidak pernah dipanggil saat halaman peta dibuka.

    python -m dapur.run semua --kerincian 240

Kontraknya di specs/001-signal-prediction-map/contracts/dapur-cli.md. Dua aturan
yang paling menentukan bentuk berkas ini:

1. Bisa dilanjutkan. Tiap langkah melewati satuan kerja yang keluarannya sudah
   ada. Perhitungan seluruh kota terlalu lama untuk diulang gara-gara laptop
   tidur di tengah jalan.
2. Hanya `unduh` yang boleh menyentuh jaringan. Kalau `hitung` boleh mengunduh,
   matematikanya tidak lagi murni dan tidak bisa diuji.
"""

import argparse
import csv
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import numpy as np

from dapur.constants import (
    COARSE_GRID_RESOLUTION_M,
    DEM_TILE_NAME,
    OPERATOR_DISPLAY_NAMES,
    SAMARINDA_BBOX,
)
from dapur.grid.build import build_grid
from dapur.grid.profile import ElevationSurface
from dapur.propagation.received_power import compute_coverage
from dapur.sources.boundary import BOUNDARY_FILENAME, download_boundary, load_boundary
from dapur.sources.buildings import download_buildings
from dapur.sources.citymap import (
    BUILDINGS_RAW,
    ROADS_RAW,
    download_extract,
    extract_city,
)
from dapur.sources.dem import download_dem
from dapur.sources.districts import (
    DISTRICT_BOUNDARIES_FILENAME,
    download_district_boundaries,
    download_districts,
)
from dapur.sources.opencellid import ARCHIVE_FILENAME, download_archive, download_current
from dapur.sources.roads import download_roads
from dapur.sources.transmitters import TransmitterSet, filter_transmitters
from dapur.tiles.archive import TileArchive, encode_png
from dapur.tiles.mercator import tile_range
from dapur.tiles.render import render_signal_tile
from dapur.tiles.summary import SUMMARY_FILENAME, build_summary, write_summary
from dapur.tiles.terrain import render_terrain_tile

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "mentah"
INTERMEDIATE_DIR = DATA_DIR / "antara"
OUTPUT_DIR = DATA_DIR / "keluaran"

TRANSMITTER_CSV = INTERMEDIATE_DIR / "pemancar-samarinda.csv"

# Jangkauan zoom bawaan.
#
# HARUS sama dengan MIN_ZOOM dan MAX_ZOOM di etalase/src/map.ts. Peta menyatakan
# `maxzoom` sumbernya dari angka itu, jadi kalau dapur berhenti lebih rendah,
# MapLibre tetap meminta ubin yang tidak pernah dibuat — dan yang muncul di zoom
# terdalam adalah kosong, bukan pesan galat.
#
# Pernah terjadi: dapur bawaannya berhenti di 14 sementara peta minta 15, dan
# arsip yang dihasilkan perintah di README sendiri tidak cukup untuk petanya.
#
# Kenapa 15 padahal kisi 30 m cuma setara zoom 12,35: lihat research.md bagian 5.
# Singkatnya, zoom di atas 13 tidak menambah keterangan, tapi menjaga batas antar
# tingkat warna tetap tajam alih-alih melebur jadi gradasi.
DEFAULT_MIN_ZOOM = 10
DEFAULT_MAX_ZOOM = 15

BYTES_PER_MB = 1_048_576

TRANSMITTER_CSV_COLUMNS = (
    "lon",
    "lat",
    "operator_id",
    "frequency_mhz",
    "antenna_height_m",
    "eirp_dbm",
)


def _grid_path(operator_id: str, resolution_m: float) -> Path:
    return INTERMEDIATE_DIR / f"kisi-{operator_id}-{int(resolution_m)}m.npz"


def _archive_path(operator_id: str) -> Path:
    return OUTPUT_DIR / f"sinyal-{operator_id}.pmtiles"


def _terrain_archive_path() -> Path:
    return OUTPUT_DIR / "ketinggian.pmtiles"


# ---------------------------------------------------------------------------
# unduh
# ---------------------------------------------------------------------------


def step_download(*, force: bool, current: bool) -> None:
    print("unduh")
    download_dem(RAW_DIR, force=force)
    if current:
        download_current(RAW_DIR, force=force)
    else:
        download_archive(RAW_DIR, force=force)
    download_boundary(RAW_DIR, force=force)
    # Nama kecamatan langsung ke folder keluaran: ia bukan bahan hitungan,
    # melainkan bagian dari yang disajikan ke peramban.
    download_districts(OUTPUT_DIR, force=force)
    # Batas poligonnya sebaliknya: bahan hitungan murni, dan terlalu besar untuk
    # dikirim ke peramban yang tidak pernah menggambarnya.
    download_district_boundaries(RAW_DIR, force=force)
    download_roads(OUTPUT_DIR, force=force)
    download_buildings(OUTPUT_DIR, force=force)
    # Gedung dan jalan lengkap datang dari ekstrak OSM, bukan Overpass:
    # 241 ribu gedung adalah penarikan massal, dan kebijakan Overpass sendiri
    # menyuruh memakai ekstrak untuk itu.
    download_extract(RAW_DIR, force=force)
    extract_city(RAW_DIR, force=force)


# ---------------------------------------------------------------------------
# siapkan
# ---------------------------------------------------------------------------


def step_prepare(*, force: bool) -> None:
    print("siapkan")
    if TRANSMITTER_CSV.exists() and not force:
        print(f"  {TRANSMITTER_CSV.name}: sudah ada, dilewati")
        return

    sumber = RAW_DIR / ARCHIVE_FILENAME
    if not sumber.exists():
        raise SystemExit(f"  {sumber} belum ada. Jalankan langkah `unduh` lebih dulu.")

    hasil = filter_transmitters(sumber)
    print(hasil.summary())

    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    tx = hasil.transmitters
    with TRANSMITTER_CSV.open("w", encoding="utf-8", newline="") as keluar:
        penulis = csv.writer(keluar)
        penulis.writerow(TRANSMITTER_CSV_COLUMNS)
        for i in range(len(tx)):
            penulis.writerow(
                [
                    tx.lon[i],
                    tx.lat[i],
                    tx.operator_id[i],
                    tx.frequency_mhz[i],
                    tx.antenna_height_m[i],
                    tx.eirp_dbm[i],
                ]
            )
    print(f"  ditulis     : {TRANSMITTER_CSV}")


def load_transmitters() -> TransmitterSet:
    """Baca kembali pemancar hasil langkah `siapkan`."""
    if not TRANSMITTER_CSV.exists():
        raise SystemExit(f"  {TRANSMITTER_CSV} belum ada. Jalankan langkah `siapkan` lebih dulu.")

    kolom: dict[str, list] = {nama: [] for nama in TRANSMITTER_CSV_COLUMNS}
    with TRANSMITTER_CSV.open(encoding="utf-8", newline="") as berkas:
        for baris in csv.DictReader(berkas):
            for nama in TRANSMITTER_CSV_COLUMNS:
                kolom[nama].append(baris[nama])

    return TransmitterSet(
        lon=np.array(kolom["lon"], dtype=float),
        lat=np.array(kolom["lat"], dtype=float),
        operator_id=np.array(kolom["operator_id"], dtype=object),
        frequency_mhz=np.array(kolom["frequency_mhz"], dtype=float),
        antenna_height_m=np.array(kolom["antenna_height_m"], dtype=float),
        eirp_dbm=np.array(kolom["eirp_dbm"], dtype=float),
    )


# ---------------------------------------------------------------------------
# hitung
# ---------------------------------------------------------------------------


def step_compute(*, resolution_m: float, operators: list[str], force: bool) -> None:
    print(f"hitung (kerincian {int(resolution_m)} m)")

    perlu = [op for op in operators if force or not _grid_path(op, resolution_m).exists()]
    for op in operators:
        if op not in perlu:
            print(f"  {op:<12} sudah ada, dilewati")
    if not perlu:
        return

    dem = RAW_DIR / f"{DEM_TILE_NAME}.tif"
    if not dem.exists():
        raise SystemExit(f"  {dem} belum ada. Jalankan langkah `unduh` lebih dulu.")

    semua = load_transmitters()
    surface = ElevationSurface.load(dem)
    grid = build_grid(SAMARINDA_BBOX, resolution_m)
    print(f"  kisi        : {grid.shape[0]} x {grid.shape[1]} = {len(grid):,} sel")

    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    for op in perlu:
        tx = semua.for_operator(op)
        mulai = time.perf_counter()
        cakupan = compute_coverage(grid, tx, surface)
        lama = time.perf_counter() - mulai

        terhitung = int(np.count_nonzero(~np.isnan(cakupan.received_power_dbm)))
        memadai = int(np.count_nonzero(cakupan.data_adequate))
        np.savez_compressed(
            _grid_path(op, resolution_m),
            received_power_dbm=cakupan.received_power_dbm,
            data_adequate=cakupan.data_adequate,
        )
        print(
            f"  {op:<12} {len(tx):>6,} pemancar | {terhitung:>8,} sel terhitung"
            f" | {memadai:>8,} sel terdata | {lama:6.1f} detik"
        )


def load_coverage(operator_id: str, resolution_m: float):
    """Baca kembali hasil hitung satu operator."""
    from dapur.propagation.received_power import Coverage

    jalur = _grid_path(operator_id, resolution_m)
    if not jalur.exists():
        raise SystemExit(f"  {jalur} belum ada. Jalankan langkah `hitung` lebih dulu.")
    isi = np.load(jalur)
    return Coverage(
        received_power_dbm=isi["received_power_dbm"],
        data_adequate=isi["data_adequate"],
    )


# ---------------------------------------------------------------------------
# ubin
# ---------------------------------------------------------------------------


def _tiles_in_range(min_zoom: int, max_zoom: int) -> Iterator[tuple[int, int, int]]:
    for zoom in range(min_zoom, max_zoom + 1):
        x1, y1, x2, y2 = tile_range(
            SAMARINDA_BBOX.min_lon,
            SAMARINDA_BBOX.min_lat,
            SAMARINDA_BBOX.max_lon,
            SAMARINDA_BBOX.max_lat,
            zoom,
        )
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                yield zoom, x, y


def _bounds() -> tuple[float, float, float, float]:
    return (
        SAMARINDA_BBOX.min_lon,
        SAMARINDA_BBOX.min_lat,
        SAMARINDA_BBOX.max_lon,
        SAMARINDA_BBOX.max_lat,
    )


def step_tiles(
    *, resolution_m: float, operators: list[str], min_zoom: int, max_zoom: int, force: bool
) -> None:
    print(f"ubin (zoom {min_zoom}-{max_zoom})")

    batas = load_boundary(RAW_DIR / BOUNDARY_FILENAME)
    grid = build_grid(SAMARINDA_BBOX, resolution_m)
    total_bita = 0

    for op in operators:
        tujuan = _archive_path(op)
        if tujuan.exists() and not force:
            print(f"  {op:<12} sudah ada, dilewati")
            total_bita += tujuan.stat().st_size
            continue

        cakupan = load_coverage(op, resolution_m)
        arsip = TileArchive(tujuan, _bounds())
        per_zoom: dict[int, int] = {}

        for zoom, x, y in _tiles_in_range(min_zoom, max_zoom):
            piksel = render_signal_tile(cakupan, grid, batas, x, y, zoom)
            if piksel is None:
                continue
            arsip.add(zoom, x, y, encode_png(piksel))
            per_zoom[zoom] = per_zoom.get(zoom, 0) + 1

        arsip.save(min_zoom, max_zoom)
        ukuran = tujuan.stat().st_size
        total_bita += ukuran
        rincian = " ".join(f"z{z}:{n}" for z, n in sorted(per_zoom.items()))
        print(f"  {op:<12} {len(arsip):>5,} ubin | {ukuran / BYTES_PER_MB:6.1f} MB | {rincian}")

    tujuan = OUTPUT_DIR / "kota.pmtiles"
    if tujuan.exists() and not force:
        print("  kota         sudah ada, dilewati")
        total_bita += tujuan.stat().st_size
    else:
        from dapur.tiles.vector import build_city_archive

        build_city_archive(RAW_DIR / BUILDINGS_RAW, RAW_DIR / ROADS_RAW, tujuan)
        total_bita += tujuan.stat().st_size

    tujuan = _terrain_archive_path()
    if tujuan.exists() and not force:
        print("  ketinggian   sudah ada, dilewati")
        total_bita += tujuan.stat().st_size
    else:
        surface = ElevationSurface.load(RAW_DIR / f"{DEM_TILE_NAME}.tif")
        arsip = TileArchive(tujuan, _bounds())
        for zoom, x, y in _tiles_in_range(min_zoom, max_zoom):
            arsip.add(zoom, x, y, encode_png(render_terrain_tile(surface, x, y, zoom)))
        arsip.save(min_zoom, max_zoom)
        ukuran = tujuan.stat().st_size
        total_bita += ukuran
        print(f"  ketinggian   {len(arsip):>5,} ubin | {ukuran / BYTES_PER_MB:6.1f} MB")

    _write_district_summary(grid, operators, resolution_m, force=force)

    print(f"  TOTAL KELUARAN: {total_bita / BYTES_PER_MB:.1f} MB")


def _write_district_summary(
    grid, operators: list[str], resolution_m: float, *, force: bool
) -> None:
    """Tulis tabel per kecamatan — cara membaca perkiraan tanpa memakai peta.

    Ikut di langkah `ubin` karena bahannya sama persis dengan yang dipakai
    menggambar ubin sinyal, dan menghitungnya dua kali cuma memboroskan waktu.
    """
    tujuan = OUTPUT_DIR / SUMMARY_FILENAME
    if tujuan.exists() and not force:
        print("  ringkasan     sudah ada, dilewati")
        return

    batas_kecamatan = json.loads(
        (RAW_DIR / DISTRICT_BOUNDARIES_FILENAME).read_text(encoding="utf-8")
    )
    ringkasan = build_summary(
        grid,
        {op: load_coverage(op, resolution_m) for op in operators},
        batas_kecamatan,
    )
    write_summary(ringkasan, OUTPUT_DIR)
    print(f"  ringkasan     {len(ringkasan['kecamatan']):>5} kecamatan")


# ---------------------------------------------------------------------------
# perangkai
# ---------------------------------------------------------------------------


def parse_zoom(teks: str) -> tuple[int, int]:
    if "-" not in teks:
        raise argparse.ArgumentTypeError("jangkauan zoom ditulis seperti 10-14")
    awal, akhir = teks.split("-", 1)
    return int(awal), int(akhir)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m dapur.run",
        description="Dapur perhitungan peta prediksi sinyal Samarinda.",
    )
    parser.add_argument(
        "langkah",
        choices=["unduh", "siapkan", "hitung", "ubin", "semua"],
        help="langkah yang dijalankan",
    )
    parser.add_argument(
        "--kerincian",
        type=float,
        default=COARSE_GRID_RESOLUTION_M,
        help=f"ukuran sel hitung dalam meter (bawaan {int(COARSE_GRID_RESOLUTION_M)})",
    )
    parser.add_argument(
        "--operator",
        choices=sorted(OPERATOR_DISPLAY_NAMES),
        action="append",
        help="batasi ke satu operator; boleh diulang",
    )
    parser.add_argument(
        "--zoom",
        type=parse_zoom,
        default=(DEFAULT_MIN_ZOOM, DEFAULT_MAX_ZOOM),
        help=f"jangkauan zoom ubin (bawaan {DEFAULT_MIN_ZOOM}-{DEFAULT_MAX_ZOOM})",
    )
    parser.add_argument(
        "--terkini",
        action="store_true",
        help="pakai data OpenCelliD terkini; perlu token di OPENCELLID_TOKEN",
    )
    parser.add_argument(
        "--paksa-ulang",
        action="store_true",
        help="kerjakan ulang walau keluarannya sudah ada",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    operators = args.operator or sorted(OPERATOR_DISPLAY_NAMES)
    min_zoom, max_zoom = args.zoom
    force = args.paksa_ulang
    mulai = time.perf_counter()

    if args.langkah in ("unduh", "semua"):
        step_download(force=force, current=args.terkini)
    if args.langkah in ("siapkan", "semua"):
        step_prepare(force=force)
    if args.langkah in ("hitung", "semua"):
        step_compute(resolution_m=args.kerincian, operators=operators, force=force)
    if args.langkah in ("ubin", "semua"):
        step_tiles(
            resolution_m=args.kerincian,
            operators=operators,
            min_zoom=min_zoom,
            max_zoom=max_zoom,
            force=force,
        )

    print(f"\nselesai dalam {time.perf_counter() - mulai:.1f} detik")
    return 0


if __name__ == "__main__":
    sys.exit(main())

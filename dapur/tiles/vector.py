"""Pemotong ubin vektor.

Menulis berkas.

Gedung dan jalan tidak bisa dikirim sebagai satu berkas: 210 ribu gedung
berukuran ratusan megabita, dan peramban akan menariknya seluruhnya walau yang
terlihat cuma satu kelurahan. Ubin vektor memecahnya per petak per zoom,
sehingga yang diambil hanya yang sedang dilihat.

Bentuknya Mapbox Vector Tile di dalam arsip PMTiles — sama seperti ubin sinyal,
jadi cara menyajikannya tidak berubah.
"""

import gzip
import json
import time
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

import mapbox_vector_tile
from pmtiles.tile import Compression, TileType
from shapely.geometry import box, shape
from shapely.strtree import STRtree

from dapur.constants import SAMARINDA_BBOX
from dapur.tiles.archive import TileArchive
from dapur.tiles.mercator import tile_bounds, tile_range

# Ukuran kisi di dalam satu ubin vektor. 4096 itu nilai baku spesifikasi MVT;
# mengubahnya cuma menambah masalah tanpa menambah ketelitian yang terlihat.
MVT_EXTENT = 4096

# Ubin dilebarkan sedikit saat memotong supaya bentuk yang melintasi tepi tidak
# terputus terlihat. Nilainya pecahan dari lebar ubin.
CLIP_MARGIN = 0.02

# Bentuk yang lebih kecil dari ini setelah dipetakan ke kisi ubin tidak akan
# terlihat, jadi dibuang. Inilah yang membuat zoom rendah tetap ringan.
MIN_PIXELS = 0.35


def read_geojsonl(path: Path) -> list[dict]:
    """Baca berkas baris-per-fitur."""
    with path.open(encoding="utf-8") as berkas:
        return [json.loads(baris) for baris in berkas if baris.strip()]


class FeatureIndex:
    """Indeks ruang supaya pencarian per ubin tidak menyapu seluruh kota."""

    def __init__(self, features: list[dict]) -> None:
        self.geometries = [shape(f["geometry"]) for f in features]
        self.properties = [f.get("properties", {}) for f in features]
        self.tree = STRtree(self.geometries)

    def __len__(self) -> int:
        return len(self.geometries)

    def query(self, kotak) -> Iterator[tuple]:
        for i in self.tree.query(kotak):
            yield self.geometries[int(i)], self.properties[int(i)]


def _to_tile_coords(geometry, west: float, south: float, east: float, north: float):
    """Pindahkan bentuk dari derajat ke kisi 0..4096 milik ubin."""
    lebar = east - west
    tinggi = north - south
    if lebar <= 0 or tinggi <= 0:
        return None

    from shapely.affinity import affine_transform

    # x' = (x - west) / lebar * extent ; y' = (y - south) / tinggi * extent
    return affine_transform(
        geometry,
        [
            MVT_EXTENT / lebar,
            0,
            0,
            MVT_EXTENT / tinggi,
            -west * MVT_EXTENT / lebar,
            -south * MVT_EXTENT / tinggi,
        ],
    )


def build_tile(
    layers: dict[str, FeatureIndex],
    x: int,
    y: int,
    zoom: int,
) -> bytes | None:
    """Susun satu ubin vektor. None kalau tidak ada apa-apa di dalamnya."""
    west, south, east, north = tile_bounds(x, y, zoom)
    margin_lon = (east - west) * CLIP_MARGIN
    margin_lat = (north - south) * CLIP_MARGIN
    potong = box(west - margin_lon, south - margin_lat, east + margin_lon, north + margin_lat)

    # Bentuk sekecil ini di kisi ubin tidak akan terlihat mata.
    ambang_luas = ((east - west) / MVT_EXTENT * MIN_PIXELS * 16) ** 2

    isi = []
    for nama, indeks in layers.items():
        fitur = []
        for geometry, properties in indeks.query(potong):
            if geometry.geom_type in ("Polygon", "MultiPolygon") and geometry.area < ambang_luas:
                continue
            terpotong = geometry.intersection(potong)
            if terpotong.is_empty:
                continue
            di_ubin = _to_tile_coords(terpotong, west, south, east, north)
            if di_ubin is None or di_ubin.is_empty:
                continue
            fitur.append({"geometry": di_ubin.wkt, "properties": properties})

        if fitur:
            isi.append({"name": nama, "features": fitur})

    if not isi:
        return None
    return mapbox_vector_tile.encode(isi, extents=MVT_EXTENT)


def tiles_covering(
    bbox: tuple[float, float, float, float], min_zoom: int, max_zoom: int
) -> Iterator[tuple[int, int, int]]:
    """Semua alamat ubin yang menutupi sebuah kotak batas."""
    west, south, east, north = bbox
    for zoom in range(min_zoom, max_zoom + 1):
        x1, y1, x2, y2 = tile_range(west, south, east, north, zoom)
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                yield zoom, x, y


# Zoom paling rendah tempat tiap kelas jalan mulai digambar.
#
# Tanpa penyaringan ini, 22 ribu gang dan jalan setapak ikut masuk ke ubin zoom
# 10 — di situ satu gang lebih tipis dari sepersepuluh piksel, jadi ia menambah
# berat tanpa menambah satu pun keterangan.
ROAD_MIN_ZOOM = {
    "motorway": 10,
    "trunk": 10,
    "primary": 10,
    "secondary": 11,
    "sungai": 10,
    "tertiary": 12,
    "residential": 13,
    "unclassified": 13,
    "living_street": 14,
    "service": 15,
    "footway": 15,
    "path": 15,
}

# Gedung baru berarti mulai zoom ini. Di bawahnya ia cuma bintik yang menutupi
# warna sinyal.
BUILDING_MIN_ZOOM = 14


def layers_for_zoom(
    buildings: FeatureIndex,
    roads_by_class: dict[str, FeatureIndex],
    zoom: int,
) -> dict[str, FeatureIndex]:
    """Lapisan apa saja yang pantas ada di satu tingkat zoom."""
    lapisan: dict[str, FeatureIndex] = {}
    if zoom >= BUILDING_MIN_ZOOM and len(buildings):
        lapisan["gedung"] = buildings
    for kelas, indeks in roads_by_class.items():
        if zoom >= ROAD_MIN_ZOOM.get(kelas, 15) and len(indeks):
            lapisan[f"jalan_{kelas}"] = indeks
    return lapisan


def build_city_archive(
    buildings_path: Path,
    roads_path: Path,
    target: Path,
    *,
    min_zoom: int = 10,
    max_zoom: int = 16,
) -> Path:
    """Potong gedung dan jalan jadi ubin vektor, bungkus ke satu arsip PMTiles."""
    print("  membaca gedung...", flush=True)
    gedung = FeatureIndex(read_geojsonl(buildings_path))

    print("  membaca jalan...", flush=True)
    per_kelas: dict[str, list[dict]] = defaultdict(list)
    for fitur in read_geojsonl(roads_path):
        per_kelas[fitur["properties"]["jenis"]].append(fitur)
    jalan = {kelas: FeatureIndex(daftar) for kelas, daftar in per_kelas.items()}

    print(f"  {len(gedung):,} gedung, {sum(len(i) for i in jalan.values()):,} jalan")

    batas = (
        SAMARINDA_BBOX.min_lon,
        SAMARINDA_BBOX.min_lat,
        SAMARINDA_BBOX.max_lon,
        SAMARINDA_BBOX.max_lat,
    )
    # Ubin vektor lazim disimpan terkompresi gzip; peramban membukanya sendiri.
    arsip = TileArchive(target, batas, tile_type=TileType.MVT, compression=Compression.GZIP)

    alamat = list(tiles_covering(batas, min_zoom, max_zoom))
    mulai = time.perf_counter()
    for nomor, (zoom, x, y) in enumerate(alamat, start=1):
        isi = build_tile(layers_for_zoom(gedung, jalan, zoom), x, y, zoom)
        if isi:
            arsip.add(zoom, x, y, gzip.compress(isi))
        if nomor % 500 == 0:
            print(
                f"    {nomor:,}/{len(alamat):,} ubin ({time.perf_counter() - mulai:.0f} detik)",
                flush=True,
            )

    arsip.save(min_zoom, max_zoom)
    print(
        f"  kota: {len(arsip):,} ubin, {target.stat().st_size / 1_048_576:.1f} MB,"
        f" {time.perf_counter() - mulai:.0f} detik"
    )
    return target

"""Pengambil gedung dan seluruh jalan Kota Samarinda.

Menyentuh jaringan (sekali, untuk mengunduh ekstrak), lalu bekerja luring.

**Kenapa bukan Overpass.** Ini sumber terberat di proyek: 210 ribu gedung.
Overpass dirancang untuk pertanyaan bertarget, bukan penarikan massal, dan
kebijakan pemakaiannya sendiri menyuruh memakai berkas ekstrak untuk hal
seperti ini. Percobaan lewat Overpass berhenti di petak kedua dari 126 dengan
HTTP 429 — dan memaksakannya berjam-jam berarti membebani layanan sukarela
sampai diblokir, yang kena ke semua orang.

Gantinya: satu berkas ekstrak Kalimantan dari Geofabrik (147 MB), diolah di
laptop. Sekali unduh, tidak membebani siapa pun, dan bisa diulang kapan saja
tanpa jaringan.
"""

import json
from pathlib import Path

import osmium

from dapur.constants import SAMARINDA_BBOX
from dapur.sources.fetch import download_file

EXTRACT_URL = "https://download.geofabrik.de/asia/indonesia/kalimantan-latest.osm.pbf"
EXTRACT_FILENAME = "kalimantan-latest.osm.pbf"

BUILDINGS_RAW = "gedung-samarinda.geojsonl"
ROADS_RAW = "jalan-lengkap.geojsonl"

# Bulatkan koordinat ke enam angka: sekitar 10 cm, jauh lebih halus daripada
# ketelitian gedung di OSM, dan memangkas ukuran berkas hampir separuh.
COORD_PRECISION = 6

# Satu cincin tertutup butuh empat titik; satu garis butuh dua.
MIN_RING_POINTS = 4
MIN_LINE_POINTS = 2

ROAD_CLASSES = frozenset(
    {
        "motorway",
        "trunk",
        "primary",
        "secondary",
        "tertiary",
        "residential",
        "unclassified",
        "service",
        "living_street",
        "footway",
        "path",
    }
)


def download_extract(dest_dir: Path, *, force: bool = False) -> Path:
    """Unduh ekstrak OSM Kalimantan. Sekali saja."""
    return download_file(
        EXTRACT_URL,
        dest_dir / EXTRACT_FILENAME,
        force=force,
        label="ekstrak OSM Kalimantan",
    )


def _levels(tags) -> int | None:
    """Jumlah lantai kalau OSM menyebutkannya. TIDAK ditebak kalau tidak ada."""
    mentah = tags.get("building:levels")
    if not mentah:
        return None
    try:
        return max(int(float(mentah)), 1)
    except ValueError:
        return None


class _CityExtractor(osmium.SimpleHandler):
    """Sapu ekstrak sekali, tulis gedung dan jalan Samarinda mengalir.

    Sekali sapu untuk dua keluaran, bukan dua kali: berkasnya 147 MB dan
    membacanya dua kali berarti menunggu dua kali tanpa alasan.

    Ditulis mengalir ke cakram, bukan ditahan di memori. 210 ribu poligon
    sebagai objek Python memakan beberapa gigabita.
    """

    def __init__(self, buildings_out, roads_out) -> None:
        super().__init__()
        self.buildings_out = buildings_out
        self.roads_out = roads_out
        self.buildings = 0
        self.roads = 0

    def _inside(self, nodes) -> bool:
        """Benar kalau ada satu titik pun di dalam kotak Samarinda."""
        for simpul in nodes:
            if not simpul.location.valid():
                continue
            if (
                SAMARINDA_BBOX.min_lon <= simpul.location.lon <= SAMARINDA_BBOX.max_lon
                and SAMARINDA_BBOX.min_lat <= simpul.location.lat <= SAMARINDA_BBOX.max_lat
            ):
                return True
        return False

    def _coords(self, nodes) -> list[list[float]]:
        return [
            [round(s.location.lon, COORD_PRECISION), round(s.location.lat, COORD_PRECISION)]
            for s in nodes
            if s.location.valid()
        ]

    def _write(self, handle, geometry_type, coords, properties) -> None:
        handle.write(
            json.dumps(
                {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": {"type": geometry_type, "coordinates": coords},
                },
                ensure_ascii=False,
            )
        )
        handle.write("\n")

    def way(self, w) -> None:
        tags = w.tags
        if "building" in tags:
            if not self._inside(w.nodes):
                return
            cincin = self._coords(w.nodes)
            if len(cincin) < MIN_RING_POINTS:
                return
            if cincin[0] != cincin[-1]:
                cincin.append(cincin[0])
            lantai = _levels(tags)
            self._write(
                self.buildings_out, "Polygon", [cincin], {"lantai": lantai} if lantai else {}
            )
            self.buildings += 1
            return

        jenis = "sungai" if tags.get("waterway") == "river" else tags.get("highway")
        if jenis and (jenis == "sungai" or jenis in ROAD_CLASSES):
            if not self._inside(w.nodes):
                return
            garis = self._coords(w.nodes)
            if len(garis) < MIN_LINE_POINTS:
                return
            self._write(self.roads_out, "LineString", garis, {"jenis": jenis})
            self.roads += 1


def extract_city(dest_dir: Path, *, force: bool = False) -> tuple[Path, Path]:
    """Saring gedung dan jalan Samarinda dari ekstrak Kalimantan.

    Returns:
        Pasangan (berkas gedung, berkas jalan), keduanya baris-per-fitur.
    """
    gedung = dest_dir / BUILDINGS_RAW
    jalan = dest_dir / ROADS_RAW

    # Keduanya harus ada. Memeriksa satu saja pernah membuat langkah ini
    # mengaku "sudah ada" lalu tetap menyapu — pesan yang membingungkan.
    if gedung.exists() and jalan.exists() and not force:
        print("  gedung & jalan Samarinda: sudah ada, dilewati")
        return gedung, jalan
    dest_dir.mkdir(parents=True, exist_ok=True)

    sumber = dest_dir / EXTRACT_FILENAME
    if not sumber.exists():
        raise SystemExit(f"  {sumber} belum ada. Jalankan langkah `unduh` lebih dulu.")

    print("  menyapu ekstrak Kalimantan, ini beberapa menit...", flush=True)
    with (
        gedung.open("w", encoding="utf-8") as gk,
        jalan.open("w", encoding="utf-8") as jk,
    ):
        penyapu = _CityExtractor(gk, jk)
        penyapu.apply_file(str(sumber), locations=True)

    print(
        f"  gedung & jalan Samarinda: {penyapu.buildings:,} gedung"
        f" ({gedung.stat().st_size / 1_048_576:.0f} MB),"
        f" {penyapu.roads:,} jalan ({jalan.stat().st_size / 1_048_576:.0f} MB)"
    )
    return gedung, jalan

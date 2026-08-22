"""Pengambil jalan utama dan sungai Kota Samarinda dari OpenStreetMap.

Menyentuh jaringan.

Nama kecamatan saja tidak cukup untuk menemukan tempat sendiri. Orang
mengenali kotanya lewat jalan yang biasa dilewati dan lewat Sungai Mahakam yang
membelahnya — dua hal itu yang membuat bentuk berwarna berubah jadi peta yang
bisa dibaca.

Yang diambil hanya jalan besar. Jalan lingkungan berjumlah puluhan ribu ruas,
dan pada zoom kota ia cuma jadi bubur garis yang menutupi datanya sendiri.
"""

import json
from pathlib import Path

from dapur.constants import SAMARINDA_OSM_RELATION_ID
from dapur.sources.fetch import DownloadError, overpass_area, overpass_json, skip_if_exists

ROADS_FILENAME = "jalan.geojson"

# Kelas jalan yang diambil, dari yang terbesar. Jalan lingkungan sengaja tidak
# ikut - lihat catatan modul.
ROAD_CLASSES = ("motorway", "trunk", "primary", "secondary")

# Ruas dengan titik lebih sedikit dari ini bukan garis.
MIN_LINE_POINTS = 2

# Bulatkan koordinat ke tujuh angka di belakang koma: sekitar satu sentimeter di
# khatulistiwa, jauh lebih halus daripada yang bisa dilihat mata di peta kota,
# dan memangkas ukuran berkas hampir separuh.
COORD_PRECISION = 7


def _query(relation_id: int) -> str:
    kelas = "|".join(ROAD_CLASSES)
    return (
        f"[out:json][timeout:170];area({overpass_area(relation_id)})->.kota;"
        f'(way(area.kota)["highway"~"^({kelas})$"];'
        f'way(area.kota)["waterway"="river"];);out geom;'
    )


def download_roads(
    dest_dir: Path,
    *,
    relation_id: int = SAMARINDA_OSM_RELATION_ID,
    force: bool = False,
) -> Path:
    """Unduh jalan utama dan sungai, simpan sebagai GeoJSON.

    Raises:
        DownloadError: kalau Overpass gagal atau tidak mengembalikan satu ruas pun.
    """
    target = dest_dir / ROADS_FILENAME
    if skip_if_exists(target, "jalan & sungai", force=force):
        return target

    jawaban = overpass_json(_query(relation_id), "jalan & sungai")

    fitur = []
    jumlah: dict[str, int] = {}
    for elemen in jawaban.get("elements", []):
        titik = elemen.get("geometry") or []
        if len(titik) < MIN_LINE_POINTS:
            continue

        tag = elemen.get("tags", {})
        jenis = "sungai" if tag.get("waterway") == "river" else tag.get("highway")
        if not jenis:
            continue

        jumlah[jenis] = jumlah.get(jenis, 0) + 1
        fitur.append(
            {
                "type": "Feature",
                "properties": {"jenis": jenis},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [round(t["lon"], COORD_PRECISION), round(t["lat"], COORD_PRECISION)]
                        for t in titik
                    ],
                },
            }
        )

    if not fitur:
        raise DownloadError("jalan & sungai: Overpass tidak mengembalikan satu ruas pun")

    target.write_text(
        json.dumps({"type": "FeatureCollection", "features": fitur}, ensure_ascii=False),
        encoding="utf-8",
    )
    rincian = " ".join(f"{k}:{v}" for k, v in sorted(jumlah.items()))
    ukuran = target.stat().st_size / 1024
    print(f"  jalan & sungai: selesai, {len(fitur)} ruas | {rincian} | {ukuran:.0f} KB")
    return target

"""Pengambil gedung pemerintahan Kota Samarinda dari OpenStreetMap.

Menyentuh jaringan.

Nama kecamatan terlalu kasar untuk menemukan tempat sendiri — satu kecamatan
bisa selebar beberapa kilometer. Kantor pemerintahan adalah patokan yang
dikenali orang Samarinda, dan OSM punya 316 di antaranya.

Disetujui di PRD bagian 14 pada 15 Agustus 2026. Ini TIDAK membatalkan
keputusan "bentang alam 3D, bukan gedung": gedungnya tetap tidak dibentuk 3D
dan tetap tidak ikut perhitungan propagasi. Perannya patokan, bukan penghalang
sinyal.
"""

import json
from pathlib import Path

from dapur.constants import SAMARINDA_OSM_RELATION_ID
from dapur.sources.fetch import DownloadError, overpass_area, overpass_json, skip_if_exists

BUILDINGS_FILENAME = "gedung-pemerintahan.geojson"

# Penanda gedung pemerintahan di OpenStreetMap. Diperiksa langsung terhadap
# Samarinda: 283 office=government, sisanya polisi, damkar, dan sejenisnya.
GOVERNMENT_TAGS = (
    '["building"="government"]',
    '["office"="government"]',
    '["amenity"~"^(townhall|courthouse|police|fire_station|public_building)$"]',
)


def _query(relation_id: int) -> str:
    bagian = "".join(f"nwr(area.kota){tag};" for tag in GOVERNMENT_TAGS)
    return (
        f"[out:json][timeout:170];area({overpass_area(relation_id)})->.kota;"
        f"({bagian});out center tags;"
    )


def download_buildings(
    dest_dir: Path,
    *,
    relation_id: int = SAMARINDA_OSM_RELATION_ID,
    force: bool = False,
) -> Path:
    """Unduh gedung pemerintahan sebagai titik bernama.

    Raises:
        DownloadError: kalau Overpass gagal atau tidak mengembalikan satu pun.

    Yang disimpan TITIK TENGAHNYA, bukan bentuk bangunannya. Pada zoom kota satu
    gedung cuma beberapa piksel, jadi bentuknya tidak terbaca sementara datanya
    sepuluh kali lebih berat. Yang menolong orang menemukan tempat adalah letak
    dan namanya.

    ponytail: titik, bukan poligon. Ganti kalau nanti zoom di atas 16 dipakai.
    """
    target = dest_dir / BUILDINGS_FILENAME
    if skip_if_exists(target, "gedung pemerintahan", force=force):
        return target

    jawaban = overpass_json(_query(relation_id), "gedung pemerintahan")

    fitur = [
        {
            "type": "Feature",
            "properties": {"nama": elemen["tags"]["name"]},
            "geometry": {
                "type": "Point",
                "coordinates": [titik["lon"], titik["lat"]],
            },
        }
        for elemen in jawaban.get("elements", [])
        # Gedung tanpa nama tidak bisa jadi patokan — ia cuma titik anonim.
        if elemen.get("tags", {}).get("name") and (titik := elemen.get("center") or elemen)
        if "lon" in titik and "lat" in titik
    ]

    if not fitur:
        raise DownloadError("gedung pemerintahan: Overpass tidak mengembalikan satu pun")

    target.write_text(
        json.dumps({"type": "FeatureCollection", "features": fitur}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  gedung pemerintahan: selesai, {len(fitur)} gedung bernama")
    return target

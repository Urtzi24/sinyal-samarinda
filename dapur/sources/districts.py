"""Pengambil daftar kecamatan Kota Samarinda dari OpenStreetMap.

Menyentuh jaringan.

Nama kecamatan dipakai supaya orang bisa menemukan daerahnya sendiri di peta.
Tanpa itu peta cuma bentuk berwarna — orang tahu ada daerah yang bagus, tapi
tidak tahu daerah mana.

Yang diambil cuma nama dan titik tengahnya, bukan batas poligonnya. Untuk
menaruh label itu sudah cukup, dan sepuluh titik jauh lebih ringan daripada
sepuluh poligon.
"""

import json
from pathlib import Path

from dapur.constants import SAMARINDA_OSM_RELATION_ID
from dapur.sources.boundary import stitch_rings
from dapur.sources.fetch import DownloadError, overpass_area, overpass_json, skip_if_exists

DISTRICTS_FILENAME = "kecamatan.json"

# Batas kecamatan disimpan terpisah dari nama dan titik tengahnya, dan tidak
# ikut ke folder keluaran. Peramban cuma perlu titik untuk menaruh label;
# poligonnya cuma dipakai dapur untuk mengelompokkan sel hitung, dan ukurannya
# ratusan kali lipat. Mengirimkannya ke peramban berarti tiap pengunjung
# mengunduh data yang tidak pernah digambar.
DISTRICT_BOUNDARIES_FILENAME = "kecamatan-batas.geojson"

# Tingkat batas administratif untuk kecamatan di OpenStreetMap Indonesia.
# Diperiksa langsung: relasi Kota Samarinda ada di tingkat 5, kecamatannya di 6.
DISTRICT_ADMIN_LEVEL = 6

EXPECTED_DISTRICT_COUNT = 10


def _query(relation_id: int, keluaran: str) -> str:
    """Kueri kecamatan Samarinda, dengan klausa `out` yang ditentukan pemanggil.

    Klausa `out`-nya sengaja utuh, bukan dirakit dari potongan. Di Overpass,
    `tags` bukan tambahan melainkan tingkat kerincian: `out geom tags` berarti
    "tag saja" dan diam-diam membuang seluruh anggota relasi, jadi poligonnya
    hilang tanpa satu pun pesan galat. Menyusunnya sebagai satu klausa membuat
    kesalahan itu tidak bisa terjadi tanpa terlihat.
    """
    return (
        f"[out:json][timeout:110];area({overpass_area(relation_id)})->.kota;"
        f'rel(area.kota)["boundary"="administrative"]'
        f'["admin_level"="{DISTRICT_ADMIN_LEVEL}"];out {keluaran};'
    )


def download_districts(
    dest_dir: Path,
    *,
    relation_id: int = SAMARINDA_OSM_RELATION_ID,
    force: bool = False,
) -> Path:
    """Unduh nama dan titik tengah tiap kecamatan.

    Raises:
        DownloadError: kalau Overpass gagal atau tidak mengembalikan kecamatan.
    """
    target = dest_dir / DISTRICTS_FILENAME
    if skip_if_exists(target, "kecamatan", force=force):
        return target

    jawaban = overpass_json(_query(relation_id, "center tags"), "kecamatan")
    kecamatan = [
        {
            "nama": elemen["tags"]["name"],
            "lon": elemen["center"]["lon"],
            "lat": elemen["center"]["lat"],
        }
        for elemen in jawaban.get("elements", [])
        if elemen.get("tags", {}).get("name") and elemen.get("center")
    ]

    if not kecamatan:
        raise DownloadError("kecamatan: Overpass tidak mengembalikan satu pun kecamatan")

    if len(kecamatan) != EXPECTED_DISTRICT_COUNT:
        # Bukan galat — batas administratif memang bisa berubah. Tapi kalau
        # jumlahnya berubah, itu perlu diketahui, bukan lewat begitu saja.
        print(
            f"  kecamatan: PERHATIAN, ditemukan {len(kecamatan)}, "
            f"biasanya {EXPECTED_DISTRICT_COUNT}"
        )

    kecamatan.sort(key=lambda k: k["nama"])
    target.write_text(json.dumps(kecamatan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  kecamatan: selesai, {len(kecamatan)} kecamatan")
    return target


def download_district_boundaries(
    dest_dir: Path,
    *,
    relation_id: int = SAMARINDA_OSM_RELATION_ID,
    force: bool = False,
) -> Path:
    """Unduh batas poligon tiap kecamatan.

    Dipakai mengelompokkan sel hitung per kecamatan untuk tabel ringkasan.
    Titik tengah saja tidak cukup: kecamatan bukan lingkaran, dan menetapkan
    sel ke kecamatan terdekat akan memindahkan sel di tepi ke kecamatan
    sebelahnya — angka yang salah di bawah nama yang benar.

    Raises:
        DownloadError: kalau Overpass gagal atau tidak ada kecamatan berpoligon.
    """
    target = dest_dir / DISTRICT_BOUNDARIES_FILENAME
    if skip_if_exists(target, "batas kecamatan", force=force):
        return target

    jawaban = overpass_json(_query(relation_id, "geom"), "batas kecamatan")

    fitur = []
    for elemen in jawaban.get("elements", []):
        nama = elemen.get("tags", {}).get("name")
        if not nama:
            continue
        luar = [
            [(titik["lon"], titik["lat"]) for titik in anggota.get("geometry", [])]
            for anggota in elemen.get("members", [])
            if anggota.get("role") == "outer" and anggota.get("geometry")
        ]
        cincin = stitch_rings(luar)
        if not cincin:
            # Satu kecamatan tanpa cincin utuh bukan alasan menggagalkan
            # semuanya, tapi harus terdengar — kecamatan itu akan hilang dari
            # tabel, dan hilang diam-diam adalah cara terburuk untuk hilang.
            print(f"  batas kecamatan: PERHATIAN, {nama} tidak punya cincin luar yang utuh")
            continue
        fitur.append(
            {
                "type": "Feature",
                "properties": {"nama": nama},
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[[list(t) for t in ring]] for ring in cincin],
                },
            }
        )

    if not fitur:
        raise DownloadError("batas kecamatan: tidak ada satu pun kecamatan berpoligon")

    fitur.sort(key=lambda f: f["properties"]["nama"])
    target.write_text(
        json.dumps({"type": "FeatureCollection", "features": fitur}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  batas kecamatan: selesai, {len(fitur)} kecamatan")
    return target

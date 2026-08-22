"""Pengambil batas wilayah Kota Samarinda dari OpenStreetMap.

Menyentuh jaringan.

Batas kota dipakai untuk dua hal: menandai bagian ubin yang berada di luar kota,
dan nanti untuk mengelompokkan perkiraan per kecamatan.

Relasinya dirujuk lewat NOMOR, bukan nama. Nama Samarinda di OSM tidak memakai
awalan "Kota", dan kueri dengan nama yang salah mengembalikan nol tanpa pesan
galat — terbaca persis seperti wilayah yang tidak ada datanya.
"""

import json
from pathlib import Path

from dapur.constants import SAMARINDA_OSM_RELATION_ID
from dapur.sources.fetch import DownloadError, overpass_json, skip_if_exists

BOUNDARY_FILENAME = "batas-samarinda.geojson"

# Satu ruas garis butuh minimal dua titik untuk punya arah.
MIN_WAY_POINTS = 2

# Satu cincin tertutup butuh minimal empat titik: tiga sudut, lalu kembali ke
# titik awal. Kurang dari itu bukan poligon, cuma garis.
MIN_RING_POINTS = 4


def stitch_rings(ways: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """Sambung potongan garis jadi cincin tertutup.

    Relasi batas di OSM tersimpan sebagai kumpulan ruas yang belum tentu urut
    dan belum tentu searah. Menggambarnya tanpa disambung menghasilkan poligon
    kusut yang tetap terlihat seperti peta.

    Dipakai batas kota maupun batas kecamatan — dua-duanya relasi OSM dengan
    bentuk yang sama.
    """
    sisa = [list(w) for w in ways if len(w) >= MIN_WAY_POINTS]
    cincin: list[list[tuple[float, float]]] = []

    while sisa:
        jalur = sisa.pop(0)
        berubah = True
        while berubah and jalur[0] != jalur[-1]:
            berubah = False
            for i, calon in enumerate(sisa):
                if calon[0] == jalur[-1]:
                    jalur.extend(calon[1:])
                elif calon[-1] == jalur[-1]:
                    jalur.extend(reversed(calon[:-1]))
                elif calon[-1] == jalur[0]:
                    jalur = calon[:-1] + jalur
                elif calon[0] == jalur[0]:
                    jalur = list(reversed(calon[1:])) + jalur
                else:
                    continue
                sisa.pop(i)
                berubah = True
                break
        if len(jalur) >= MIN_RING_POINTS:
            if jalur[0] != jalur[-1]:
                jalur.append(jalur[0])
            cincin.append(jalur)
    return cincin


def download_boundary(
    dest_dir: Path,
    *,
    relation_id: int = SAMARINDA_OSM_RELATION_ID,
    force: bool = False,
) -> Path:
    """Unduh batas kota dan simpan sebagai GeoJSON.

    Raises:
        DownloadError: kalau Overpass gagal atau relasinya tidak punya batas.
    """
    target = dest_dir / BOUNDARY_FILENAME
    if skip_if_exists(target, "batas kota", force=force):
        return target

    jawaban = overpass_json(f"[out:json][timeout:170];rel({relation_id});out geom;", "batas kota")
    elemen = jawaban.get("elements") or []
    if not elemen:
        raise DownloadError(f"batas kota: relasi {relation_id} tidak ditemukan di OSM")

    luar = [
        [(titik["lon"], titik["lat"]) for titik in anggota.get("geometry", [])]
        for anggota in elemen[0].get("members", [])
        if anggota.get("role") == "outer" and anggota.get("geometry")
    ]
    cincin = stitch_rings(luar)
    if not cincin:
        raise DownloadError(f"batas kota: relasi {relation_id} tidak punya cincin luar yang utuh")

    geojson = {
        "type": "MultiPolygon",
        "coordinates": [[[list(t) for t in ring]] for ring in cincin],
    }
    target.write_text(json.dumps(geojson), encoding="utf-8")
    print(f"  batas kota: selesai, {len(cincin)} cincin")
    return target


def load_boundary(path: Path) -> dict:
    """Baca GeoJSON batas kota."""
    return json.loads(path.read_text(encoding="utf-8"))

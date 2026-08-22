"""Ringkasan perkiraan per kecamatan.

Fungsi murni, kecuali satu penulis berkas di bawah.

**Kenapa ada.** Peta warna tidak bisa dibaca semua orang. Yang memakai pembaca
layar tidak mendapat apa-apa dari gradasi biru-kehijauan, dan yang buta warna
mendapat lebih sedikit daripada yang dikira perancangnya. FR-013 mewajibkan
perkiraan yang SAMA tersedia tanpa memakai peta — bukan versi ringkas, bukan
tautan ke halaman lain, melainkan angka yang sama dalam bentuk yang bisa dibaca
berurutan.

**Kenapa tiga angka, bukan satu.** Satu kecamatan bisa bagus di separuh
wilayahnya dan buruk di separuhnya lagi. Menyebut satu angka tengah untuk
seluruh kecamatan akan menyembunyikan persis hal yang paling ingin diketahui
orang yang sedang mencari kos. Jadi yang dilaporkan tengahnya sekaligus
rentangnya.

**Yang sengaja tidak dihitung di sini: tingkat warnanya.** Ambang antar tingkat
tinggal di `etalase/src/palette.ts`, satu tempat. Kalau dihitung juga di sini,
ambangnya jadi tinggal di dua tempat dalam dua bahasa, dan tabel bisa
mengatakan "tingkat 4" untuk warna yang di peta tampil tingkat 3. Dapur cuma
mengirim dBm; peramban yang menerjemahkannya, memakai ambang yang sama persis
dengan yang mewarnai petanya.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import shape

from dapur.grid.build import Grid
from dapur.propagation.received_power import Coverage

SUMMARY_FILENAME = "ringkasan-kecamatan.json"

# Persentil bawah dan atas yang dilaporkan sebagai rentang.
#
# Bukan nilai terendah dan tertinggi: satu sel tunggal di dasar jurang atau di
# puncak bukit akan menarik rentangnya jadi lebar dan tidak berarti. Sepuluh
# persen di tiap ujung membuang kasus ekstrem itu sambil tetap menunjukkan
# betapa jauh jaraknya antara bagian terbaik dan terburuk kecamatan.
LOWER_PERCENTILE = 10
UPPER_PERCENTILE = 90


@dataclass(frozen=True)
class DistrictCoverage:
    """Perkiraan satu operator di satu kecamatan.

    `dbm_*` bernilai None kalau tidak ada satu pun sel berdata memadai — itu
    keadaan yang berbeda dari sinyal lemah, dan tidak boleh disamarkan jadi
    angka.
    """

    dbm_tengah: float | None
    dbm_bawah: float | None
    dbm_atas: float | None
    sel: int
    sel_memadai: int


def district_mask(grid: Grid, geometry: dict) -> np.ndarray:
    """Sel kisi mana yang jatuh di dalam satu kecamatan.

    Memakai poligon sebenarnya, bukan kedekatan ke titik tengah. Kecamatan
    bukan lingkaran dan luasnya jauh berbeda; menetapkan sel ke titik tengah
    terdekat memindahkan seluruh tepi wilayah ke kecamatan sebelahnya.
    """
    poligon = shape(geometry)
    shapely.prepare(poligon)
    return shapely.contains_xy(poligon, grid.lon, grid.lat)


def summarize_district(coverage: Coverage, di_kecamatan: np.ndarray) -> DistrictCoverage:
    """Ringkas daya terima satu operator di dalam satu kecamatan."""
    sel = int(np.count_nonzero(di_kecamatan))

    # Sel yang datanya tidak memadai tetap DIHITUNG sebagai bagian kecamatan,
    # tapi angkanya tidak ikut. Daya terima di sel begitu tidak salah — ia tidak
    # punya arti sama sekali, karena tidak ada menara terdaftar cukup dekat.
    terpakai = di_kecamatan & coverage.data_adequate & ~np.isnan(coverage.received_power_dbm)
    nilai = coverage.received_power_dbm[terpakai]
    if nilai.size == 0:
        return DistrictCoverage(None, None, None, sel, 0)

    bawah, tengah, atas = np.percentile(nilai, [LOWER_PERCENTILE, 50, UPPER_PERCENTILE])
    return DistrictCoverage(
        dbm_tengah=round(float(tengah), 1),
        dbm_bawah=round(float(bawah), 1),
        dbm_atas=round(float(atas), 1),
        sel=sel,
        sel_memadai=int(nilai.size),
    )


def build_summary(
    grid: Grid,
    coverages: dict[str, Coverage],
    districts: dict,
) -> dict:
    """Rangkai ringkasan seluruh kecamatan untuk seluruh operator.

    Args:
        grid: kisi hitung yang dipakai menghasilkan `coverages`.
        coverages: daya terima per operator, kunci sama dengan id operator.
        districts: FeatureCollection batas kecamatan.

    Kecamatan yang tidak memuat satu pun sel kisi dibuang, bukan dilaporkan
    kosong — itu berarti batasnya di luar kotak hitung, bukan berarti tidak ada
    sinyal di sana.
    """
    keluaran = []
    for fitur in districts.get("features", []):
        nama = fitur["properties"]["nama"]
        di_kecamatan = district_mask(grid, fitur["geometry"])
        if not di_kecamatan.any():
            print(f"  ringkasan: PERHATIAN, {nama} tidak memuat satu pun sel kisi")
            continue

        keluaran.append(
            {
                "nama": nama,
                "operator": {
                    op: vars(summarize_district(cakupan, di_kecamatan))
                    for op, cakupan in coverages.items()
                },
            }
        )

    keluaran.sort(key=lambda k: k["nama"])
    return {"kerincian_m": int(grid.resolution_m), "kecamatan": keluaran}


def write_summary(summary: dict, dest_dir: Path) -> Path:
    """Tulis ringkasan ke folder keluaran."""
    target = dest_dir / SUMMARY_FILENAME
    target.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
    return target

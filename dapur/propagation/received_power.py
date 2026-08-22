"""Perangkai daya terima per sel.

Menggabungkan ruang bebas, difraksi medan, dan daftar pemancar jadi satu angka
per sel: daya terima dari pemancar terkuat.

**Terkuat, bukan dijumlahkan.** Ponsel menempel ke satu sel, bukan menggabungkan
daya semua menara di sekitarnya. Menjumlahkan akan membuat daerah padat menara
terlihat jauh lebih baik dari kenyataan.
"""

from dataclasses import dataclass

import numpy as np

from dapur.constants import RECEIVER_HEIGHT_M, TRANSMITTER_SEARCH_BUFFER_M
from dapur.grid.build import Grid
from dapur.grid.profile import ElevationSurface, terrain_profile
from dapur.propagation.diffraction import deygout_loss_db
from dapur.propagation.free_space import free_space_loss_db, wavelength_m
from dapur.sources.transmitters import TransmitterSet

# Berapa pemancar terbaik per sel yang dihitung difraksinya.
#
# Menghitung difraksi untuk SEMUA pasangan pemancar-sel tidak mungkin: 21.000 sel
# dikali 3.000 pemancar sudah 63 juta profil medan. Jadi disaring dulu.
#
# Penyaringnya berdasar sifat yang pasti: difraksi hanya bisa MENGURANGI daya,
# tidak pernah menambah. Jadi daya tanpa difraksi adalah batas atas, dan
# pemancar yang batas atasnya sudah jauh di bawah pemenang sementara tidak
# mungkin menang setelah dikurangi.
#
# Delapan adalah ambang praktis, bukan jaminan. Kalau delapan pemancar teratas
# semuanya terhalang berat sementara yang kesembilan lapang, hasilnya meleset.
# Kemungkinannya kecil dan biayanya besar, jadi ini pertukaran yang diterima —
# tapi ia pertukaran, bukan kebenaran.
CANDIDATE_TRANSMITTERS_PER_CELL = 8

# Sel dihitung sekaligus per rombongan supaya matriks jarak tidak meledak.
# 63 juta pasangan sebagai float64 butuh sekitar 500 MB; per rombongan 2.000 sel
# angkanya turun ke puluhan MB.
CELL_CHUNK = 2_000

# Jarak paling dekat yang boleh dipakai menghitung. Sel yang jatuh tepat di
# posisi pemancar akan menghasilkan pembagian nol.
MIN_DISTANCE_M = 1.0

# Kalau pemancar terdekat milik sebuah operator lebih jauh dari ini, wilayah itu
# dianggap TIDAK TERDATA — bukan bersinyal lemah.
#
# Lima kilometer diambil dari jari-jari sel makro pedesaan di Report ITU-R
# M.2292-0 (lebih dari 3 km, angka lazim 5 km untuk pita 1-2 GHz). Kalau sel
# makro pedesaan sekalipun tidak akan mencapai sejauh itu, yang terjadi bukan
# sinyal lemah melainkan menara yang tidak terdaftar.
DATA_ADEQUATE_RADIUS_M = 5_000.0


@dataclass
class Coverage:
    """Hasil hitung satu operator di seluruh kisi."""

    received_power_dbm: np.ndarray
    data_adequate: np.ndarray

    @property
    def shape(self) -> tuple[int, ...]:
        return self.received_power_dbm.shape


def compute_coverage(
    grid: Grid,
    transmitters: TransmitterSet,
    surface: ElevationSurface,
    *,
    max_range_m: float = TRANSMITTER_SEARCH_BUFFER_M,
    candidates: int = CANDIDATE_TRANSMITTERS_PER_CELL,
) -> Coverage:
    """Hitung daya terima untuk tiap sel kisi.

    Args:
        grid: kisi hitung.
        transmitters: pemancar satu operator saja.
        surface: raster ketinggian.
        max_range_m: pemancar lebih jauh dari ini diabaikan.
        candidates: berapa pemancar teratas yang dihitung difraksinya.

    Returns:
        Daya terima per sel dalam dBm, dan penanda kecukupan data.

    Sel tanpa pemancar dalam jangkauan mendapat NaN, bukan angka kecil. Angka
    kecil terbaca sebagai sinyal lemah; NaN terbaca sebagai tidak ada data — dan
    dua hal itu wajib bisa dibedakan di peta.
    """
    bentuk = grid.shape
    daya = np.full(grid.lon.size, np.nan, dtype=float)
    memadai = np.zeros(grid.lon.size, dtype=bool)

    if len(transmitters) == 0:
        return Coverage(daya.reshape(bentuk), memadai.reshape(bentuk))

    tx_x, tx_y = grid.projection.to_metric(transmitters.lon, transmitters.lat)
    tx_lambda = np.asarray(wavelength_m(transmitters.frequency_mhz), dtype=float)

    sel_x = grid.x_m.ravel()
    sel_y = grid.y_m.ravel()
    sel_lon = grid.lon.ravel()
    sel_lat = grid.lat.ravel()

    for awal in range(0, sel_x.size, CELL_CHUNK):
        akhir = min(awal + CELL_CHUNK, sel_x.size)
        potong = slice(awal, akhir)

        mendatar = np.hypot(
            sel_x[potong, None] - tx_x[None, :],
            sel_y[potong, None] - tx_y[None, :],
        )

        # Jarak MIRING, bukan mendatar. Sel tepat di bawah antena setinggi 25 m
        # berjarak 25 m dari antenanya, bukan nol. Memakai jarak mendatar
        # membuat sel di dekat menara menerima daya yang mustahil — sempat
        # menghasilkan +13 dBm, padahal ponsel tidak pernah menerima di atas
        # sekitar -40 dBm.
        beda_tinggi = transmitters.antenna_height_m[None, :] - RECEIVER_HEIGHT_M
        jarak = np.hypot(mendatar, beda_tinggi)
        np.maximum(jarak, MIN_DISTANCE_M, out=jarak)

        # Kecukupan data diukur dari jarak MENDATAR: pertanyaannya "adakah
        # menara terdata di sekitar sini", bukan seberapa jauh sinyalnya jalan.
        memadai[potong] = np.any(mendatar <= DATA_ADEQUATE_RADIUS_M, axis=1)

        dalam_jangkauan = jarak <= max_range_m
        if not dalam_jangkauan.any():
            continue

        rugi_ruang_bebas = np.asarray(
            free_space_loss_db(jarak, transmitters.frequency_mhz[None, :]), dtype=float
        )
        batas_atas = transmitters.eirp_dbm[None, :] - rugi_ruang_bebas
        batas_atas = np.where(dalam_jangkauan, batas_atas, -np.inf)

        jumlah_calon = min(candidates, batas_atas.shape[1])
        teratas = np.argpartition(-batas_atas, jumlah_calon - 1, axis=1)[:, :jumlah_calon]

        for baris_lokal in range(batas_atas.shape[0]):
            indeks_sel = awal + baris_lokal
            terbaik = -np.inf

            for kolom in teratas[baris_lokal]:
                atas = batas_atas[baris_lokal, kolom]
                if not np.isfinite(atas) or atas <= terbaik:
                    continue

                jarak_ini = float(jarak[baris_lokal, kolom])
                jarak_profil, ketinggian = terrain_profile(
                    surface,
                    float(transmitters.lon[kolom]),
                    float(transmitters.lat[kolom]),
                    float(sel_lon[indeks_sel]),
                    float(sel_lat[indeks_sel]),
                    jarak_ini,
                )
                rugi_difraksi = deygout_loss_db(
                    jarak_profil,
                    ketinggian,
                    tx_height_m=float(transmitters.antenna_height_m[kolom]),
                    rx_height_m=RECEIVER_HEIGHT_M,
                    wavelength_m=float(tx_lambda[kolom]),
                )
                nilai = atas - rugi_difraksi
                terbaik = max(terbaik, nilai)

            if np.isfinite(terbaik):
                daya[indeks_sel] = terbaik

    return Coverage(daya.reshape(bentuk), memadai.reshape(bentuk))

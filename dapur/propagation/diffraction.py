"""Difraksi mata pisau menurut ITU-R P.526, dan penggabungan Deygout.

Fungsi murni — Prinsip III.

Inilah bagian yang membuat peta ini menjelaskan **sebab**, bukan cuma hasil.
Tanpa difraksi medan, sebuah daerah cuma bisa dikatakan jelek; dengan difraksi,
bisa ditunjukkan bukit mana yang membuatnya jelek.

Sumber: Recommendation ITU-R P.526-14 (01/2018), "Propagation by diffraction",
bagian 4.1:

    pers. (26)  nu = h * sqrt( (2/lambda) * (1/d1 + 1/d2) )
    pers. (31)  J(nu) = 6,9 + 20 log10( sqrt((nu - 0,1)^2 + 1) + nu - 0,1 )  dB
                berlaku untuk nu > -0,78
"""

import numpy as np

# Batas keberlakuan pers. (31), disebut langsung di teks rekomendasi: di bawah
# nilai ini pendekatannya berhenti masuk akal. Rumusnya sendiri meluruh ke nol
# persis di sini, jadi memotongnya di sini tidak menimbulkan lompatan.
#
# Sumber: ITU-R P.526-14 bagian 4.1, kalimat pengantar pers. (31).
NU_VALIDITY_LIMIT = -0.78

# Tetapan pers. (31). Ditulis bernama supaya tidak ada angka telanjang di badan
# rumus — Prinsip II. Ketiganya milik persamaan itu, bukan hasil penyetelan.
J_OFFSET_DB = 6.9
J_SHIFT = 0.1

# Berapa dalam penggabungan Deygout boleh menelusuri penghalang bersarang.
#
# Tiga adalah praktik lazim: penghalang utama, ditambah satu di tiap sisi. Lebih
# dalam dari itu menambah waktu hitung tanpa menambah ketelitian yang berarti,
# karena sumbangan tiap lapis makin kecil.
DEYGOUT_MAX_DEPTH = 3

# Titik paling sedikit yang membuat sebuah profil bisa punya penghalang: dua
# ujung, ditambah minimal satu titik di antaranya. Sel yang sangat dekat dengan
# menara menghasilkan profil sependek ini.
MIN_PROFILE_POINTS = 3


def fresnel_kirchoff_parameter(
    obstacle_height_m: float | np.ndarray,
    d1_m: float | np.ndarray,
    d2_m: float | np.ndarray,
    wavelength_m: float | np.ndarray,
) -> float | np.ndarray:
    """Parameter difraksi Fresnel-Kirchoff, ITU-R P.526-14 pers. (26).

    Args:
        obstacle_height_m: tinggi puncak penghalang di atas garis lurus yang
            menghubungkan kedua ujung lintasan. **Negatif kalau di bawah garis
            itu** — tanda ini menentukan segalanya.
        d1_m: jarak ujung pertama lintasan ke puncak penghalang, meter.
        d2_m: jarak ujung kedua lintasan ke puncak penghalang, meter.
        wavelength_m: panjang gelombang, meter.

    Rekomendasi mensyaratkan satuan yang saling konsisten. Di sini semuanya
    meter, jadi tidak ada faktor pengubah satuan yang bisa tertinggal.
    """
    d1 = np.asarray(d1_m, dtype=float)
    d2 = np.asarray(d2_m, dtype=float)
    if np.any(d1 <= 0) or np.any(d2 <= 0):
        raise ValueError("kedua jarak ke penghalang harus lebih besar dari nol")

    wavelength = np.asarray(wavelength_m, dtype=float)
    if np.any(wavelength <= 0):
        raise ValueError("panjang gelombang harus lebih besar dari nol")

    height = np.asarray(obstacle_height_m, dtype=float)
    nu = height * np.sqrt((2.0 / wavelength) * (1.0 / d1 + 1.0 / d2))

    if np.isscalar(obstacle_height_m) and np.isscalar(d1_m) and np.isscalar(d2_m):
        return float(nu)
    return nu


def knife_edge_loss_db(nu: float | np.ndarray) -> float | np.ndarray:
    """Redaman difraksi mata pisau tunggal, ITU-R P.526-14 pers. (31).

    Nol untuk nu di bawah batas keberlakuan: lintasan yang lapang tidak
    kehilangan apa pun. Nilai negatif tidak pernah dikembalikan — bukit yang
    menguatkan sinyal akan terlihat masuk akal di peta sambil salah sepenuhnya.
    """
    values = np.asarray(nu, dtype=float)
    shifted = values - J_SHIFT
    loss = J_OFFSET_DB + 20.0 * np.log10(np.sqrt(shifted**2 + 1.0) + shifted)
    loss = np.where(values > NU_VALIDITY_LIMIT, loss, 0.0)
    loss = np.maximum(loss, 0.0)

    if np.isscalar(nu):
        return float(loss)
    return loss


def _height_above_line(
    distances_m: np.ndarray,
    elevations_m: np.ndarray,
    tx_height_m: float,
    rx_height_m: float,
) -> np.ndarray:
    """Tinggi tiap titik profil di atas garis lurus pemancar-penerima.

    Garisnya ditarik dari puncak antena pemancar ke puncak antena penerima,
    bukan dari permukaan tanah — itu sebabnya tinggi antena ikut masuk.
    """
    total_distance = distances_m[-1] - distances_m[0]
    if total_distance <= 0:
        raise ValueError("profil medan harus punya panjang lebih besar dari nol")

    start = elevations_m[0] + tx_height_m
    end = elevations_m[-1] + rx_height_m
    fraction = (distances_m - distances_m[0]) / total_distance
    line = start + (end - start) * fraction
    return elevations_m - line


def deygout_loss_db(
    distances_m: np.ndarray,
    elevations_m: np.ndarray,
    tx_height_m: float,
    rx_height_m: float,
    wavelength_m: float,
    _depth: int = 0,
) -> float:
    """Redaman difraksi seluruh lintasan dengan penggabungan Deygout.

    Cara kerjanya: cari penghalang paling menentukan di sepanjang lintasan —
    yang parameter nu-nya terbesar — hitung redamannya, lalu ulangi hal yang
    sama pada dua potongan lintasan di kiri dan kanannya. Sumbangan tiap lapis
    dijumlahkan.

    Metode: J. Deygout, "Multiple knife-edge diffraction of microwaves",
    IEEE Transactions on Antennas and Propagation, 1966. Redaman tiap penghalang
    tunggal memakai ITU-R P.526-14 pers. (31).

    Yang dihitung sebagai penghalang hanya **puncak** — titik yang tidak lebih
    rendah dari kedua tetangganya. Alasannya ada di badan fungsi; singkatnya,
    tanpa syarat itu tanah datar pun akan terbaca meredam.

    **Dua penyederhanaan yang diketahui untuk Tahap A:**

    1. ITU-R P.526-14 bagian 4.3 memberi suku koreksi untuk kasus dua penghalang
       terpisah (pers. 39). Belum diterapkan; redaman lintasan berpenghalang
       banyak cenderung ditaksir agak berlebih.
    2. Difraksi bumi bulat (P.526 bagian 3) tidak dihitung sama sekali. Pada
       lintasan yang benar-benar datar dan panjang, redaman ditaksir agak
       kurang.

    Keduanya tercatat sebagai penghalusan yang menunggu, bukan cacat tersembunyi.

    Args:
        distances_m: jarak tiap titik cuplik dari pemancar, menaik.
        elevations_m: ketinggian tanah di tiap titik cuplik.
        tx_height_m: tinggi antena pemancar di atas tanah.
        rx_height_m: tinggi antena penerima di atas tanah.
        wavelength_m: panjang gelombang, meter.
        _depth: kedalaman penelusuran; dipakai internal, jangan diisi pemanggil.

    Returns:
        Redaman difraksi total dalam dB. Nol kalau lintasannya lapang.
    """
    if _depth >= DEYGOUT_MAX_DEPTH:
        return 0.0

    if distances_m.size < MIN_PROFILE_POINTS:
        return 0.0

    heights = _height_above_line(distances_m, elevations_m, tx_height_m, rx_height_m)

    # Ujung-ujungnya adalah antena itu sendiri, bukan penghalang.
    inner = slice(1, -1)
    d1 = distances_m[inner] - distances_m[0]
    d2 = distances_m[-1] - distances_m[inner]

    nu = np.asarray(
        fresnel_kirchoff_parameter(
            obstacle_height_m=heights[inner],
            d1_m=d1,
            d2_m=d2,
            wavelength_m=wavelength_m,
        )
    )

    # Hanya PUNCAK yang boleh dihitung sebagai penghalang.
    #
    # Tanpa syarat ini, tanah datar pun meredam: di dekat penerima yang cuma
    # setinggi 1,5 m, permukaan tanah memang masuk ke zona Fresnel, dan tiap
    # titik cuplik akan terbaca sebagai mata pisau. Lintasan datar sepanjang
    # 10 km jadi kehilangan belasan dB tanpa satu pun bukit — dan angka itu
    # terlihat masuk akal, jadi tidak ada yang akan curiga.
    #
    # Tanah datar memang meredam lebih dari ruang bebas, tapi itu difraksi bumi
    # bulat (ITU-R P.526 bagian 3), model yang lain sama sekali dan di luar
    # lingkup Tahap A.
    is_local_peak = (heights[inner] >= heights[:-2]) & (heights[inner] >= heights[2:])
    if not np.any(is_local_peak):
        return 0.0

    nu_at_peaks = np.where(is_local_peak, nu, -np.inf)
    peak = int(np.argmax(nu_at_peaks))
    peak_nu = float(nu_at_peaks[peak])
    if peak_nu <= NU_VALIDITY_LIMIT:
        return 0.0

    loss = float(knife_edge_loss_db(peak_nu))
    index = peak + 1  # kembali ke penomoran profil utuh

    # Puncak penghalang utama jadi ujung bagi kedua potongan lintasan. Tingginya
    # sudah termasuk medan, jadi tinggi antena tambahan pada ujung itu nol.
    obstacle_top = 0.0
    loss += deygout_loss_db(
        distances_m[: index + 1],
        elevations_m[: index + 1],
        tx_height_m,
        obstacle_top,
        wavelength_m,
        _depth + 1,
    )
    loss += deygout_loss_db(
        distances_m[index:],
        elevations_m[index:],
        obstacle_top,
        rx_height_m,
        wavelength_m,
        _depth + 1,
    )
    return loss

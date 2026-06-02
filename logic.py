import numpy as np
import pandas as pd

# ==========================================
# KONSTANTA GLOBAL KRITERIA
# ==========================================
KRITERIA_COLS = [
    'C1_KK_Serumah', 'C2_Pendidikan', 'C3_Anggota_Kel', 'C4_Masih_Sekolah',
    'C5_Pengeluaran', 'C6_Penghasilan', 'C7_Kondisi_Rumah',
    'C8_Tanggungan_Khusus', 'C9_Jarak_Fasilitas'
]

# True = benefit (semakin besar semakin baik), False = cost (semakin kecil semakin baik)
TIPE_BENEFIT = [True, False, True, True, False, False, False, True, True]


# ==========================================
# FUNGSI KALKULASI
# ==========================================

def hitung_SAW(matrix: np.ndarray, bobot: np.ndarray, tipe_benefit: list):
    """
    Menghitung skor SAW (Simple Additive Weighting).

    Args:
        matrix      : np.ndarray bentuk (n_kandidat, n_kriteria)
        bobot       : np.ndarray bobot ternormalisasi
        tipe_benefit: list bool — True = benefit, False = cost

    Returns:
        norm  : matriks ternormalisasi
        skor  : skor akhir SAW per kandidat
    """
    norm = np.zeros_like(matrix, dtype=float)
    for j in range(matrix.shape[1]):
        col = matrix[:, j]
        if tipe_benefit[j]:
            norm[:, j] = col / col.max() if col.max() != 0 else 0
        else:
            norm[:, j] = col.min() / col if col.min() != 0 else 0
    skor = norm.dot(bobot)
    return norm, skor


def hitung_TOPSIS(matrix: np.ndarray, bobot: np.ndarray, tipe_benefit: list):
    """
    Menghitung skor TOPSIS (Technique for Order Preference by Similarity to Ideal Solution).

    Args:
        matrix      : np.ndarray bentuk (n_kandidat, n_kriteria)
        bobot       : np.ndarray bobot ternormalisasi
        tipe_benefit: list bool — True = benefit, False = cost

    Returns:
        norm_vec  : matriks normalisasi vektor
        weighted  : matriks terbobot
        ideal_pos : solusi ideal positif
        ideal_neg : solusi ideal negatif
        d_pos     : jarak ke solusi ideal positif per kandidat
        d_neg     : jarak ke solusi ideal negatif per kandidat
        skor      : skor preferensi akhir TOPSIS per kandidat
    """
    norm_vec = matrix / np.sqrt((matrix ** 2).sum(axis=0) + 1e-9)
    weighted = norm_vec * bobot
    ideal_pos = np.zeros(matrix.shape[1])
    ideal_neg = np.zeros(matrix.shape[1])

    for j in range(matrix.shape[1]):
        if tipe_benefit[j]:
            ideal_pos[j] = weighted[:, j].max()
            ideal_neg[j] = weighted[:, j].min()
        else:
            ideal_pos[j] = weighted[:, j].min()
            ideal_neg[j] = weighted[:, j].max()

    d_pos = np.sqrt(((weighted - ideal_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_neg) ** 2).sum(axis=1))
    skor = d_neg / (d_pos + d_neg + 1e-9)
    return norm_vec, weighted, ideal_pos, ideal_neg, d_pos, d_neg, skor


def hitung_BORDA(rank_dm1_series: pd.Series, rank_dm2_series: pd.Series, n_kandidat: int):
    """
    Menghitung agregasi Borda dari dua peringkat DM.

    Args:
        rank_dm1_series : pd.Series peringkat dari DM1 (SAW)
        rank_dm2_series : pd.Series peringkat dari DM2 (TOPSIS)
        n_kandidat      : jumlah total kandidat

    Returns:
        borda_dm1 : poin Borda DM1
        borda_dm2 : poin Borda DM2
        total     : total poin Borda agregasi
    """
    borda_dm1 = (n_kandidat - rank_dm1_series).values
    borda_dm2 = (n_kandidat - rank_dm2_series).values
    return borda_dm1, borda_dm2, borda_dm1 + borda_dm2


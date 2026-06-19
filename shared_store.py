"""
shared_store.py — Memori Global Server untuk GDSS Bansos
=========================================================
Menggunakan @st.cache_resource sehingga satu objek dictionary ini
hidup di memori proses Streamlit dan bisa diakses serta dimodifikasi
secara in-place oleh semua tab dan semua user secara simultan.

Karena dict adalah mutable, setiap perubahan pada isinya (misalnya
shared_data["w1"]["C1"] = 0.5) langsung terlihat oleh seluruh session
tanpa perlu cache invalidation.
"""

import streamlit as st


# ---------------------------------------------------------------------------
# SHARED MEMORY UTAMA
# ---------------------------------------------------------------------------

@st.cache_resource
def get_shared_data() -> dict:
    """
    Mengembalikan satu-satunya instance dictionary bersama di memori server.

    Struktur:
        "w1"       : dict bobot DM1 (Dinsos)  -> {"C1": float, "C2": float, "C3": float}
        "w2"       : dict bobot DM2 (Camat)   -> {"C1": float, "C2": float, "C3": float}
        "kandidat" : list[dict] data kandidat -> [{"Nama": str, "C1": float, ...}, ...]

    Returns:
        dict: Objek bersama yang dapat dimodifikasi in-place dari modul mana pun.
    """
    return {
        # Bobot awal DM1 (Kepala Dinsos) — metode SAW
        "w1": {
            "C1": 0.33,
            "C2": 0.33,
            "C3": 0.34,
        },
        # Bobot awal DM2 (Camat) — metode TOPSIS
        "w2": {
            "C1": 0.33,
            "C2": 0.33,
            "C3": 0.34,
        },
        # Data mentah simulasi kandidat bansos (nilai C1–C3 skala 0–100)
        "kandidat": [
            {"Nama": "Budi Santoso",  "C1": 80, "C2": 60, "C3": 70},
            {"Nama": "Siti Rahayu",   "C1": 90, "C2": 50, "C3": 85},
            {"Nama": "Ahmad Fauzi",   "C1": 70, "C2": 75, "C3": 65},
        ],
    }


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def update_bobot(state_key: str, new_weights: dict) -> None:
    """
    Memperbarui bobot di shared memory secara in-place.

    Karena cache_resource mengembalikan objek yang sama setiap kali
    dipanggil, modifikasi di sini langsung terlihat oleh semua tab.

    Args:
        state_key   : "w1" (Dinsos) atau "w2" (Camat)
        new_weights : dict {"C1": float, "C2": float, "C3": float}
    """
    shared = get_shared_data()
    shared[state_key].update(new_weights)


def get_bobot(state_key: str) -> dict:
    """
    Mengambil snapshot bobot terkini dari shared memory.

    Args:
        state_key : "w1" atau "w2"

    Returns:
        dict {"C1": float, "C2": float, "C3": float}
    """
    return get_shared_data()[state_key]

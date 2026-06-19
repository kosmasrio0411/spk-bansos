import streamlit as st
from streamlit_option_menu import option_menu

# ==============================================================================
# 1. SHARED STORAGE (MEMORI BERSAMA ANTAR-TAB & ANTAR-USER)
# Didelegasikan ke shared_store.py agar satu instance cache_resource digunakan
# secara konsisten oleh seluruh modul (components.py, app.py, dsb.).
# ==============================================================================
from shared_store import get_shared_data

# ==============================================================================
# 2. AUTENTIKASI — Didelegasikan ke auth.py
# ==============================================================================
from auth import init_session_state, login_page, logout

# ==============================================================================
# 3. HALAMAN-HALAMAN APLIKASI
# Didelegasikan ke components.py agar menggunakan shared_store real-time.
# ==============================================================================
from components import (
    halaman_kelola_data,
    halaman_panel_preferensi,
    halaman_papan_hasil,
)

# ==========================================
# KONFIGURASI HALAMAN (Harus paling atas)
# ==========================================
st.set_page_config(
    page_title="GDSS Bansos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inisialisasi Session State
init_session_state()

# Cek Status Login
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ==========================================
# SIDEBAR: INFO USER & NAVIGASI
# ==========================================
with st.sidebar:
    st.markdown(
        "<h2 style='text-align: center; color: #2c3e50;'>Sistem Bantuan Sosial</h2>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Info pengguna yang sedang login
    st.markdown(f"**Login sebagai:** `{st.session_state.username}`")
    st.markdown(f"**Role:** `{st.session_state.role}`")

    if st.button("🚪 Logout", use_container_width=True):
        logout()

    st.markdown("---")

    # Peta ikon per halaman
    icon_map = {
        "Kelola Data Kandidat": "folder-fill",
        "Panel DM1: Dinsos":    "people-fill",
        "Panel DM2: Camat":     "person-fill",
        "Papan Hasil Agregasi": "bar-chart-fill",
    }

    # Menu navigasi — hanya menampilkan halaman sesuai role pengguna
    halaman = option_menu(
        menu_title="Navigasi Utama",
        options=st.session_state.allowed_pages,
        icons=[icon_map[p] for p in st.session_state.allowed_pages],
        menu_icon="cast",
        default_index=0,
        styles={
            "container":        {"padding": "0!important", "background-color": "transparent"},
            "icon":             {"color": "gray", "font-size": "18px"},
            "nav-link": {
                "font-size":    "15px",
                "text-align":   "left",
                "margin":       "5px",
                "--hover-color": "#e0e0e0",
            },
            "nav-link-selected": {"background-color": "#2c3e50", "color": "white"},
        }
    )

# ==========================================
# ROUTING HALAMAN
# ==========================================
if halaman == "Kelola Data Kandidat":
    halaman_kelola_data()

elif halaman == "Panel DM1: Dinsos":
    halaman_panel_preferensi(
        judul="👥 Panel Preferensi: Kepala Dinsos (DM1)",
        metode="SAW",
        state_key="w1"
    )

elif halaman == "Panel DM2: Camat":
    halaman_panel_preferensi(
        judul="👤 Panel Preferensi: Camat (DM2)",
        metode="TOPSIS",
        state_key="w2"
    )

elif halaman == "Papan Hasil Agregasi":
    halaman_papan_hasil()
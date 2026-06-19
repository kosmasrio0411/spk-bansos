"""
auth.py — Modul Autentikasi GDSS Bansos
=========================================
Menyediakan:
    - USERS                : Konfigurasi kredensial dan hak akses per role
    - _get_dummy_data()    : Data kandidat dummy 30 orang, 9 kriteria
    - init_session_state() : Inisialisasi seluruh st.session_state aplikasi
    - login_page()         : UI form login berbasis text_input + password
    - logout()             : Reset state dan redirect ke halaman login
"""

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# KONFIGURASI AKUN PENGGUNA
# ---------------------------------------------------------------------------

USERS: dict[str, dict] = {
    "admin": {
        "password": "admin123",
        "role": "Administrator",
        "display_name": "Admin",
        "allowed_pages": [
            "Kelola Data Kandidat",
            "Papan Hasil Agregasi",
        ],
    },
    "dinsos": {
        "password": "dinsos123",
        "role": "Kepala Dinas Sosial",
        "display_name": "Kepala Dinsos",
        "allowed_pages": [
            "Panel DM1: Dinsos",
            "Papan Hasil Agregasi",
        ],
    },
    "camat": {
        "password": "camat123",
        "role": "Camat",
        "display_name": "Camat",
        "allowed_pages": [
            "Panel DM2: Camat",
            "Papan Hasil Agregasi",
        ],
    },
}


# ---------------------------------------------------------------------------
# DATA KANDIDAT DUMMY (30 orang, 9 kriteria)
# ---------------------------------------------------------------------------

def _get_dummy_data() -> pd.DataFrame:
    """Mengembalikan DataFrame data kandidat dummy untuk inisialisasi awal."""
    data_kandidat = {
        'Nama': [
            'Budi Santoso', 'Siti Rahayu', 'Ahmad Fauzi', 'Dewi Lestari', 'Hendra Wijaya',
            'Sumiati', 'Bambang Purnomo', 'Rina Kusuma', 'Joko Susilo', 'Murniati',
            'Agus Setiawan', 'Tutik Handayani', 'Wahyu Nugroho', 'Sri Mulyani', 'Darmanto',
            'Endang Sulistyo', 'Rudi Hartono', 'Fatimah', 'Suryo Atmojo', 'Lasmi',
            'Prasetyo', 'Karyati', 'Dwi Cahyono', 'Suparni', 'Eko Widodo',
            'Yanti Wulandari', 'Sugiyono', 'Marni', 'Tri Handoko', 'Winarti'
        ],
        'Desa': [
            'Ngemplak', 'Ngemplak', 'Tegalsari', 'Tegalsari', 'Purwosari',
            'Purwosari', 'Karanganyar', 'Karanganyar', 'Ngemplak', 'Tegalsari',
            'Purwosari', 'Karanganyar', 'Ngemplak', 'Tegalsari', 'Purwosari',
            'Karanganyar', 'Ngemplak', 'Tegalsari', 'Purwosari', 'Karanganyar',
            'Ngemplak', 'Tegalsari', 'Purwosari', 'Karanganyar', 'Ngemplak',
            'Tegalsari', 'Purwosari', 'Karanganyar', 'Ngemplak', 'Tegalsari'
        ],
        'C1_KK_Serumah':       [2,1,3,1,2, 1,3,2,1,2, 3,1,2,1,3, 2,1,2,3,1, 2,3,1,2,1, 3,2,1,2,3],
        'C2_Pendidikan':       [4,3,5,2,4, 5,3,4,2,5, 4,3,5,2,4, 3,5,4,3,5, 4,3,5,4,3, 5,4,3,2,4],
        'C3_Anggota_Kel':      [5,3,7,2,4, 6,5,3,2,7, 4,3,6,2,5, 4,7,3,5,6, 4,6,3,5,2, 7,4,3,5,6],
        'C4_Masih_Sekolah':    [2,1,3,1,2, 3,2,1,0,4, 2,1,3,1,2, 2,4,1,2,3, 2,3,1,2,0, 4,2,1,2,3],
        'C5_Pengeluaran':      [350,500,280,600,400, 250,450,550,650,200, 380,520,260,580,420,
                                480,220,560,340,190, 410,270,530,370,610, 210,440,590,320,240],
        'C6_Penghasilan':      [400,600,300,700,450, 280,500,620,720,230, 420,580,280,640,470,
                                530,240,620,380,210, 460,290,590,410,680, 230,490,650,360,260],
        'C7_Kondisi_Rumah':    [4,2,5,2,3, 5,3,2,1,5, 4,2,5,3,4, 3,5,2,4,5, 3,5,2,4,1, 5,3,2,4,5],
        'C8_Tanggungan_Khusus':[1,0,2,0,1, 2,1,0,0,2, 1,0,2,0,1, 1,2,0,1,2, 1,2,0,1,0, 2,1,0,1,2],
        'C9_Jarak_Fasilitas':  [2.5,1.0,4.0,0.5,3.0, 5.0,2.0,1.5,0.8,6.0, 3.5,1.2,4.5,0.7,3.8,
                                2.2,5.5,1.8,2.8,6.5, 3.2,4.8,1.3,2.7,0.6, 6.2,2.5,1.7,3.1,5.8],
    }
    return pd.DataFrame(data_kandidat)


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

def init_session_state() -> None:
    """
    Menginisialisasi seluruh key st.session_state yang dibutuhkan aplikasi.
    Harus dipanggil sekali di awal app.py sebelum pengecekan login.
    Aman dipanggil berulang — hanya mengisi key yang belum ada.
    """
    # --- State autentikasi ---
    auth_defaults = {
        "logged_in":    False,
        "username":     "",
        "role":         "",
        "allowed_pages": [],
    }
    for key, val in auth_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # --- State data aplikasi ---
    if "df" not in st.session_state:
        st.session_state.df = _get_dummy_data()
    if "w1" not in st.session_state:
        # Bobot mentah DM1 (Dinsos) — 9 elemen sesuai KRITERIA_COLS di logic.py
        st.session_state.w1 = [0.05, 0.10, 0.05, 0.08, 0.25, 0.27, 0.08, 0.07, 0.05]
    if "w2" not in st.session_state:
        # Bobot mentah DM2 (Camat) — 9 elemen sesuai KRITERIA_COLS di logic.py
        st.session_state.w2 = [0.10, 0.12, 0.10, 0.15, 0.10, 0.11, 0.15, 0.12, 0.05]
    if "kuota" not in st.session_state:
        st.session_state.kuota = 3


# ---------------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------------

def logout() -> None:
    """
    Mereset seluruh state autentikasi ke kondisi awal dan memuat ulang
    halaman sehingga pengguna kembali ke layar login.
    """
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.allowed_pages = []
    st.rerun()


# ---------------------------------------------------------------------------
# HALAMAN LOGIN
# ---------------------------------------------------------------------------

def login_page() -> None:
    """
    Menampilkan form login dengan st.text_input untuk Username dan
    st.text_input(type='password') untuk Password.

    Alur:
        1. User mengisi form dan klik "Login".
        2. Jika credentials cocok → isi session_state → st.rerun().
        3. Jika credentials salah atau field kosong → st.error().
    """
    # ── Layout terpusat ────────────────────────────────────────────────────
    _, col_center, _ = st.columns([1, 1.4, 1])

    with col_center:
        # Header
        st.markdown(
            """
            <div style="text-align:center; padding: 2rem 0 1rem;">
                <h1 style="font-size:2.4rem; margin-bottom:0.25rem;">📊 GDSS Bansos</h1>
                <p style="color:#6b7280; font-size:1rem; margin-top:0;">
                    Group Decision Support System — Penerima Bantuan Sosial
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Form login
        with st.form(key="login_form", clear_on_submit=False):
            st.subheader("🔐 Masuk ke Sistem")

            username_input = st.text_input(
                label="Username",
                placeholder="Masukkan username Anda",
                key="input_username",
            )
            password_input = st.text_input(
                label="Password",
                placeholder="Masukkan password Anda",
                type="password",
                key="input_password",
            )

            submitted = st.form_submit_button(
                "🚀 Login",
                use_container_width=True,
                type="primary",
            )

        # ── Validasi credentials ───────────────────────────────────────────
        if submitted:
            # Cek field kosong
            if not username_input.strip() or not password_input.strip():
                st.error("⚠️ Username dan Password tidak boleh kosong.")

            # Cek username terdaftar
            elif username_input not in USERS:
                st.error("❌ Username tidak ditemukan. Periksa kembali username Anda.")

            # Cek password
            elif password_input != USERS[username_input]["password"]:
                st.error("❌ Password salah. Silakan coba lagi.")

            # Login berhasil
            else:
                user_data = USERS[username_input]
                st.session_state.logged_in    = True
                st.session_state.username     = username_input
                st.session_state.role         = user_data["role"]
                st.session_state.allowed_pages = user_data["allowed_pages"]
                st.success(f"✅ Login berhasil! Selamat datang, **{user_data['display_name']}**.")
                st.rerun()

        # ── Tabel info akun demo ───────────────────────────────────────────
        st.markdown("---")
        st.info(
            """
**🗝️ Akun Demo yang Tersedia:**

| Role | Username | Password | Akses Halaman |
|---|---|---|---|
| Administrator | `admin` | `admin123` | Semua halaman |
| Kepala Dinas Sosial | `dinsos` | `dinsos123` | Kelola Data, Panel DM1, Papan Hasil |
| Camat | `camat` | `camat123` | Panel DM2, Papan Hasil |
            """
        )

import streamlit as st
import pandas as pd


# ==========================================
# KONFIGURASI USER & ROLE
# ==========================================
USERS = {
    "admin": {
        "password": "admin123",
        "role": "Admin/Operator",
        "allowed_pages": ["Kelola Data Kandidat", "Papan Hasil Agregasi"]
    },
    "dinsos": {
        "password": "dm1123",
        "role": "DM1 Dinsos",
        "allowed_pages": ["Panel DM1: Dinsos", "Papan Hasil Agregasi"]
    },
    "camat": {
        "password": "dm2123",
        "role": "DM2 Camat",
        "allowed_pages": ["Panel DM2: Camat", "Papan Hasil Agregasi"]
    }
}


def _get_dummy_data() -> pd.DataFrame:
    """Mengembalikan data kandidat dummy untuk inisialisasi awal."""
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
        'C1_KK_Serumah':      [2,1,3,1,2, 1,3,2,1,2, 3,1,2,1,3, 2,1,2,3,1, 2,3,1,2,1, 3,2,1,2,3],
        'C2_Pendidikan':      [4,3,5,2,4, 5,3,4,2,5, 4,3,5,2,4, 3,5,4,3,5, 4,3,5,4,3, 5,4,3,2,4],
        'C3_Anggota_Kel':     [5,3,7,2,4, 6,5,3,2,7, 4,3,6,2,5, 4,7,3,5,6, 4,6,3,5,2, 7,4,3,5,6],
        'C4_Masih_Sekolah':   [2,1,3,1,2, 3,2,1,0,4, 2,1,3,1,2, 2,4,1,2,3, 2,3,1,2,0, 4,2,1,2,3],
        'C5_Pengeluaran':     [350,500,280,600,400, 250,450,550,650,200, 380,520,260,580,420, 480,220,560,340,190, 410,270,530,370,610, 210,440,590,320,240],
        'C6_Penghasilan':     [400,600,300,700,450, 280,500,620,720,230, 420,580,280,640,470, 530,240,620,380,210, 460,290,590,410,680, 230,490,650,360,260],
        'C7_Kondisi_Rumah':   [4,2,5,2,3, 5,3,2,1,5, 4,2,5,3,4, 3,5,2,4,5, 3,5,2,4,1, 5,3,2,4,5],
        'C8_Tanggungan_Khusus':[1,0,2,0,1, 2,1,0,0,2, 1,0,2,0,1, 1,2,0,1,2, 1,2,0,1,0, 2,1,0,1,2],
        'C9_Jarak_Fasilitas': [2.5,1.0,4.0,0.5,3.0, 5.0,2.0,1.5,0.8,6.0, 3.5,1.2,4.5,0.7,3.8, 2.2,5.5,1.8,2.8,6.5, 3.2,4.8,1.3,2.7,0.6, 6.2,2.5,1.7,3.1,5.8]
    }
    return pd.DataFrame(data_kandidat)


# ==========================================
# INISIALISASI SESSION STATE
# ==========================================
def init_session_state():
    """
    Menginisialisasi seluruh session state yang dibutuhkan aplikasi.
    Harus dipanggil sekali di awal main.py sebelum pengecekan login.
    """
    # --- State autentikasi ---
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "allowed_pages" not in st.session_state:
        st.session_state.allowed_pages = []

    # --- State data aplikasi ---
    if "df" not in st.session_state:
        st.session_state.df = _get_dummy_data()
    if "w1" not in st.session_state:
        # Bobot mentah DM1 (Dinsos) — akan dinormalisasi sebelum kalkulasi
        st.session_state.w1 = [0.05, 0.10, 0.05, 0.08, 0.25, 0.27, 0.08, 0.07, 0.05]
    if "w2" not in st.session_state:
        # Bobot mentah DM2 (Camat) — akan dinormalisasi sebelum kalkulasi
        st.session_state.w2 = [0.10, 0.12, 0.10, 0.15, 0.10, 0.11, 0.15, 0.12, 0.05]
    if "kuota" not in st.session_state:
        st.session_state.kuota = 3


# ==========================================
# HALAMAN LOGIN
# ==========================================
def login_page():
    """Menampilkan UI form login lengkap dengan informasi akun demo."""
    st.markdown(
        "<h1 style='text-align:center;'>🔐 Login GDSS Bansos</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center;'>Silakan login sesuai peran pengguna.</p>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login", use_container_width=True)

            if login_button:
                if username in USERS and password == USERS[username]["password"]:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = USERS[username]["role"]
                    st.session_state.allowed_pages = USERS[username]["allowed_pages"]
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("Username atau password salah.")

    st.markdown("---")
    st.info("""
    **Akun Demo:**

    | Role | Username | Password |
    |---|---|---|
    | Admin/Operator | `admin` | `admin123` |
    | DM1 Dinsos | `dinsos` | `dm1123` |
    | DM2 Camat | `camat` | `dm2123` |
    """)


# ==========================================
# LOGOUT
# ==========================================
def logout():
    """Mereset seluruh state autentikasi dan memuat ulang halaman."""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.allowed_pages = []
    st.rerun()

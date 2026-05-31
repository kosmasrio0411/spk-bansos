import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from streamlit_option_menu import option_menu

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="GDSS Bansos", page_icon="📊", layout="wide")

# ==========================================
# 1. INISIALISASI DATA & SESSION STATE
# ==========================================
kriteria_cols = ['C1_KK_Serumah','C2_Pendidikan','C3_Anggota_Kel','C4_Masih_Sekolah',
                 'C5_Pengeluaran','C6_Penghasilan','C7_Kondisi_Rumah','C8_Tanggungan_Khusus','C9_Jarak_Fasilitas']
tipe_benefit = [True, False, True, True, False, False, False, True, False]

def get_dummy_data():
    data_kandidat = {
        'Nama': ['Budi Santoso', 'Siti Rahayu', 'Ahmad Fauzi', 'Dewi Lestari', 'Hendra Wijaya'],
        'Desa': ['Ngemplak', 'Ngemplak', 'Tegalsari', 'Tegalsari', 'Purwosari'],
        'C1_KK_Serumah':      [2, 1, 3, 1, 2],
        'C2_Pendidikan':      [4, 3, 5, 2, 4],
        'C3_Anggota_Kel':     [5, 3, 7, 2, 4],
        'C4_Masih_Sekolah':   [2, 1, 3, 1, 2],
        'C5_Pengeluaran':     [350, 500, 280, 600, 400],
        'C6_Penghasilan':     [400, 600, 300, 700, 450],
        'C7_Kondisi_Rumah':   [4, 2, 5, 2, 3],
        'C8_Tanggungan_Khusus':[1, 0, 2, 0, 1],
        'C9_Jarak_Fasilitas': [2.5, 1.0, 4.0, 0.5, 3.0]
    }
    return pd.DataFrame(data_kandidat)

# Simpan data ke memori sementara (Session State)
if 'df' not in st.session_state:
    st.session_state.df = get_dummy_data()
if 'w1' not in st.session_state:
    st.session_state.w1 = [0.05, 0.10, 0.05, 0.08, 0.25, 0.27, 0.08, 0.07, 0.05]
if 'w2' not in st.session_state:
    st.session_state.w2 = [0.10, 0.12, 0.10, 0.15, 0.10, 0.11, 0.15, 0.12, 0.05]
if 'kuota' not in st.session_state:
    st.session_state.kuota = 3

# ==========================================
# 2. FUNGSI PERHITUNGAN
# ==========================================
def hitung_SAW(matrix, bobot, tipe_benefit):
    norm = np.zeros_like(matrix, dtype=float)
    for j in range(matrix.shape[1]):
        col = matrix[:, j]
        if tipe_benefit[j]:
            norm[:, j] = col / col.max() if col.max() != 0 else 0
        else:
            norm[:, j] = col.min() / col if col.min() != 0 else 0
    skor = norm.dot(bobot)
    return norm, skor

def hitung_TOPSIS(matrix, bobot, tipe_benefit):
    norm_vec = matrix / np.sqrt((matrix ** 2).sum(axis=0) + 1e-9) 
    weighted = norm_vec * bobot
    ideal_pos, ideal_neg = np.zeros(matrix.shape[1]), np.zeros(matrix.shape[1])
    
    for j in range(matrix.shape[1]):
        if tipe_benefit[j]:
            ideal_pos[j], ideal_neg[j] = weighted[:, j].max(), weighted[:, j].min()
        else:
            ideal_pos[j], ideal_neg[j] = weighted[:, j].min(), weighted[:, j].max()
            
    d_pos = np.sqrt(((weighted - ideal_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_neg) ** 2).sum(axis=1))
    skor = d_neg / (d_pos + d_neg + 1e-9)
    return norm_vec, weighted, ideal_pos, ideal_neg, d_pos, d_neg, skor

def hitung_BORDA(rank_dm1_series, rank_dm2_series, n_kandidat):
    borda_dm1 = (n_kandidat - rank_dm1_series).values
    borda_dm2 = (n_kandidat - rank_dm2_series).values
    return borda_dm1, borda_dm2, borda_dm1 + borda_dm2

def simulasi_sensitivitas(matrix, tipe_benefit, bobot_base_dm1, bobot_base_dm2, idx_kriteria, n_steps=10):
    hasil = []
    delta_range = np.linspace(0.01, 0.40, n_steps)
    
    for delta in delta_range:
        #Modifikasi bobot DM1
        w1 = bobot_base_dm1.copy()
        sisa1 = 1 - delta
        total_lain1 = w1.sum() - w1[idx_kriteria]
        if total_lain1 > 0:
            w1 = w1 * (sisa1 / total_lain1)
        w1[idx_kriteria] = delta
        
        #Modifikasi bobot DM2
        w2 = bobot_base_dm2.copy()
        sisa2 = 1 - delta
        total_lain2 = w2.sum() - w2[idx_kriteria]
        if total_lain2 > 0:
            w2 = w2 * (sisa2 / total_lain2)
        w2[idx_kriteria] = delta
        
        _, s_saw = hitung_SAW(matrix, w1, tipe_benefit)
        *_, s_topsis = hitung_TOPSIS(matrix, w2, tipe_benefit)
        
        rank_s = pd.Series(s_saw).rank(ascending=False).astype(int)
        rank_t = pd.Series(s_topsis).rank(ascending=False).astype(int)
        _, _, b_tot = hitung_BORDA(rank_s, rank_t, len(matrix))
        
        top3_idx = np.argsort(-b_tot)[:3]
        hasil.append({
            'bobot': delta,
            'top1': top3_idx[0],
            'top2': top3_idx[1],
            'top3': top3_idx[2]
        })
    return hasil

# ==========================================
# 3. NAVIGASI HALAMAN (OPTION MENU)
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #2c3e50;'>Sistem Bantuan Sosial</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    halaman = option_menu(
        menu_title="Navigasi Utama",
        options=["Kelola Data Kandidat", "Panel DM1: Dinsos", "Panel DM2: Camat", "Papan Hasil Agregasi"],
        # Ikon Dinsos (berdua) dan Camat (tunggal) sudah disesuaikan
        icons=["folder-fill", "people-fill", "person-fill", "bar-chart-fill"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "gray", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "15px", 
                "text-align": "left", 
                "margin":"5px", 
                "--hover-color": "#e0e0e0"
            },
            "nav-link-selected": {"background-color": "#2c3e50", "color": "white", "icon-color": "white"},
        }
    )

# ==========================================
# HALAMAN 1: KELOLA DATA
# ==========================================
if halaman == "Kelola Data Kandidat":
    st.title("📋 Kelola Data Kandidat Bansos")
    st.markdown("Halaman ini diasumsikan diakses oleh **Admin Desa/Operator** untuk memasukkan data warga.")
    
    sumber_data = st.radio("Pilih metode input data:", ["Data Dummy Bawaan", "Input Manual Terbuka"], horizontal=True)
    
    if sumber_data == "Data Dummy Bawaan":
        st.session_state.df = get_dummy_data()
        df_tampil = st.session_state.df.copy()
        df_tampil.index = np.arange(1, len(df_tampil) + 1)
        df_tampil.index.name = 'No.'
        st.dataframe(df_tampil, use_container_width=True)
        st.success(f"Data Dummy aktif. Total kandidat: {len(df_tampil)}.")
        
    elif sumber_data == "Input Manual Terbuka":
        st.info("✏️ Edit tabel di bawah ini. Tekan Enter setelah mengubah nilai. Anda juga bisa menambah baris baru di bagian bawah.")
        df_edit = st.session_state.df.copy()
        df_edit.index = np.arange(1, len(df_edit) + 1)
        df_edit.index.name = 'No.'
        
        updated_df = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)
        st.session_state.df = updated_df

    st.markdown("---")
    st.session_state.kuota = st.number_input("Tentukan Kuota Penerima Bantuan:", min_value=1, value=st.session_state.kuota)

# ==========================================
# HALAMAN 2: PANEL DM 1
# ==========================================
elif halaman == "Panel DM1: Dinsos":
    st.title("👥 Panel Preferensi: Kepala Dinsos (DM1)")
    st.markdown("Silakan atur bobot tingkat kepentingan untuk setiap kriteria. Sistem menggunakan metode **SAW**.")
    
    col_kiri, col_kanan = st.columns([2, 1])
    
    with col_kiri:
        st.subheader("Atur Slider Bobot Mentah")
        for i, col in enumerate(kriteria_cols):
            st.session_state.w1[i] = st.slider(
                f"{col}", 0.0, 1.0, float(st.session_state.w1[i]), 0.01, key=f"dm1_slider_{i}"
            )
            
    with col_kanan:
        st.subheader("Bobot Aktif")
        w1_norm = np.array(st.session_state.w1) / np.sum(st.session_state.w1) if np.sum(st.session_state.w1) > 0 else np.ones(9)/9
        df_w1 = pd.DataFrame({'Kriteria': kriteria_cols, 'Bobot Normalisasi': np.round(w1_norm, 4)})
        df_w1.index = np.arange(1, len(df_w1) + 1)
        df_w1.index.name = 'No.'
        st.dataframe(df_w1, use_container_width=True)

# ==========================================
# HALAMAN 3: PANEL DM 2
# ==========================================
elif halaman == "Panel DM2: Camat":
    st.title("👤 Panel Preferensi: Camat (DM2)")
    st.markdown("Silakan atur bobot tingkat kepentingan untuk setiap kriteria. Sistem menggunakan metode **TOPSIS**.")
    
    col_kiri, col_kanan = st.columns([2, 1])
    
    with col_kiri:
        st.subheader("Atur Slider Bobot Mentah")
        for i, col in enumerate(kriteria_cols):
            st.session_state.w2[i] = st.slider(
                f"{col}", 0.0, 1.0, float(st.session_state.w2[i]), 0.01, key=f"dm2_slider_{i}"
            )
            
    with col_kanan:
        st.subheader("Bobot Aktif")
        w2_norm = np.array(st.session_state.w2) / np.sum(st.session_state.w2) if np.sum(st.session_state.w2) > 0 else np.ones(9)/9
        df_w2 = pd.DataFrame({'Kriteria': kriteria_cols, 'Bobot Normalisasi': np.round(w2_norm, 4)})
        df_w2.index = np.arange(1, len(df_w2) + 1)
        df_w2.index.name = 'No.'
        st.dataframe(df_w2, use_container_width=True)

# ==========================================
# HALAMAN 4: PAPAN HASIL
# ==========================================
elif halaman == "Papan Hasil Agregasi":
    st.title("🏆 Papan Hasil Agregasi GDSS")
    
    df = st.session_state.df.copy()
    if df.empty:
        st.error("⚠️ Data Kandidat kosong. Silakan isi data di Halaman 1 terlebih dahulu.")
    else:
        missing_cols = [col for col in kriteria_cols if col not in df.columns]
        if missing_cols:
            st.error(f"⚠️ Data Anda tidak valid. Kolom berikut hilang: {', '.join(missing_cols)}")
        else:
            KUOTA = st.session_state.kuota
            if KUOTA > len(df):
                KUOTA = len(df)
            
            w1_norm = np.array(st.session_state.w1) / np.sum(st.session_state.w1) if np.sum(st.session_state.w1) > 0 else np.ones(9)/9
            w2_norm = np.array(st.session_state.w2) / np.sum(st.session_state.w2) if np.sum(st.session_state.w2) > 0 else np.ones(9)/9
            
            matrix = df[kriteria_cols].values.astype(float)
            
            # --- EKSEKUSI ---
            _, skor_saw = hitung_SAW(matrix, w1_norm, tipe_benefit)
            df_saw = df[['Nama']].copy()
            df_saw['Skor_SAW'] = skor_saw
            df_saw['Rank_SAW'] = df_saw['Skor_SAW'].rank(ascending=False).astype(int)

            _, _, _, _, _, _, skor_topsis = hitung_TOPSIS(matrix, w2_norm, tipe_benefit)
            df_topsis = df[['Nama']].copy()
            df_topsis['Skor_TOPSIS'] = skor_topsis
            df_topsis['Rank_TOPSIS'] = df_topsis['Skor_TOPSIS'].rank(ascending=False).astype(int)

            df_borda = df[['Nama', 'Desa']].copy()
            df_borda['Rank_SAW'] = df_saw['Rank_SAW'].values
            df_borda['Rank_TOPSIS'] = df_topsis['Rank_TOPSIS'].values
            _, _, b_total = hitung_BORDA(df_borda['Rank_SAW'], df_borda['Rank_TOPSIS'], len(df))
            df_borda['Total_Borda'] = b_total
            df_borda['Rank_Final'] = df_borda['Total_Borda'].rank(ascending=False).astype(int)
            
            df_borda = df_borda.sort_values('Rank_Final')
            top_kandidat = df_borda.head(KUOTA)

            # --- TABEL HASIL ---
            st.subheader(f"Top {KUOTA} Penerima Bantuan Sosial Prioritas (Agregasi Borda)")
            top_tampil = top_kandidat.copy()
            top_tampil.index = np.arange(1, len(top_tampil) + 1)
            top_tampil.index.name = 'No.'
            st.dataframe(top_tampil.style.highlight_min(subset=['Rank_Final'], color='lightgreen'), use_container_width=True)

            with st.expander("Lihat Peringkat Detail (SAW & TOPSIS)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Hasil Individu DM1 (SAW)**")
                    saw_tampil = df_saw.sort_values('Rank_SAW').copy()
                    saw_tampil.index = np.arange(1, len(saw_tampil) + 1)
                    saw_tampil.index.name = 'No.'
                    st.dataframe(saw_tampil, use_container_width=True)
                with col2:
                    st.markdown("**Hasil Individu DM2 (TOPSIS)**")
                    topsis_tampil = df_topsis.sort_values('Rank_TOPSIS').copy()
                    topsis_tampil.index = np.arange(1, len(topsis_tampil) + 1)
                    topsis_tampil.index.name = 'No.'
                    st.dataframe(topsis_tampil, use_container_width=True)

            # ==========================================
            # VISUALISASI KE BAWAH
            # ==========================================
            st.markdown("---")
            st.header("📊 Analisis Visualisasi GDSS")

            # Plot 1: Skor (Bukan Rank)
            st.subheader("1. Perbandingan Skor Normalisasi (SAW vs TOPSIS)")
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            nama_sorted = df_borda['Nama'].values
            skor_saw_sorted = df_saw.set_index('Nama').loc[nama_sorted, 'Skor_SAW'].values
            skor_topsis_sorted = df_topsis.set_index('Nama').loc[nama_sorted, 'Skor_TOPSIS'].values
            x = np.arange(len(nama_sorted))
            w = 0.35
            ax1.bar(x - w/2, skor_saw_sorted, w, label='SAW (DM1-Dinsos)', color='steelblue')
            ax1.bar(x + w/2, skor_topsis_sorted, w, label='TOPSIS (DM2-Camat)', color='darkorange')
            ax1.set_xticks(x)
            ax1.set_xticklabels([n.split()[0] for n in nama_sorted], rotation=45)
            ax1.set_ylabel('Skor Akhir')
            ax1.legend()
            ax1.grid(axis='y', alpha=0.3)
            st.pyplot(fig1)

            # Plot 2: Total Borda Score
            st.subheader("2. Total Skor Borda Kandidat")
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            colors = ['gold' if i < KUOTA else 'lightgray' for i in range(len(df_borda))]
            ax2.barh(range(len(df_borda)), df_borda['Total_Borda'].values, color=colors)
            ax2.set_yticks(range(len(df_borda)))
            ax2.set_yticklabels([f"{r}. {n.split()[0]}" for r, n in zip(df_borda['Rank_Final'], df_borda['Nama'])])
            ax2.invert_yaxis()
            ax2.set_xlabel('Total Borda Score')
            patch_a = mpatches.Patch(color='gold', label=f'Lolos Kuota ({KUOTA})')
            patch_b = mpatches.Patch(color='lightgray', label='Belum lolos')
            ax2.legend(handles=[patch_a, patch_b])
            ax2.grid(axis='x', alpha=0.3)
            st.pyplot(fig2)

            # Plot 3: Selisih Rank
            st.subheader("3. Selisih Peringkat SAW vs TOPSIS")
            fig3, ax3 = plt.subplots(figsize=(10, 5))
            df_borda['Delta_Rank'] = (df_borda['Rank_SAW'] - df_borda['Rank_TOPSIS']).abs()
            df_borda_sorted_delta = df_borda.sort_values('Delta_Rank', ascending=False)
            colors3 = ['tomato' if d > 2 else 'steelblue' for d in df_borda_sorted_delta['Delta_Rank']]
            ax3.barh(range(len(df_borda_sorted_delta)), df_borda_sorted_delta['Delta_Rank'].values, color=colors3)
            ax3.set_yticks(range(len(df_borda_sorted_delta)))
            ax3.set_yticklabels(df_borda_sorted_delta['Nama'].apply(lambda x: x.split()[0]))
            ax3.invert_yaxis()
            ax3.set_xlabel('|Rank SAW - Rank TOPSIS|')
            ax3.axvline(x=2, color='red', linestyle='--', alpha=0.5, label='Batas Perlu Diskusi (>2)')
            ax3.legend()
            ax3.grid(axis='x', alpha=0.3)
            st.pyplot(fig3)

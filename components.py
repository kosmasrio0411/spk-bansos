import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st

from logic import (
    KRITERIA_COLS,
    TIPE_BENEFIT,
    hitung_SAW,
    hitung_TOPSIS,
    hitung_BORDA,
)

# ==========================================
# HALAMAN 1: KELOLA DATA KANDIDAT
# ==========================================
def halaman_kelola_data():
    """Halaman untuk Admin/Operator mengelola data kandidat penerima Bansos."""
    st.title("📋 Kelola Data Kandidat Bansos")
    st.markdown(
        "Halaman ini diakses oleh **Admin Desa/Operator** "
        "untuk memasukkan data warga calon penerima bantuan sosial."
    )

    sumber_data = st.radio(
        "Pilih metode input data:",
        ["Data Dummy Bawaan", "Input Manual Terbuka"],
        horizontal=True
    )

    if sumber_data == "Data Dummy Bawaan":
        from auth import _get_dummy_data
        st.session_state.df = _get_dummy_data()
        df_tampil = st.session_state.df.copy()
        df_tampil.index = np.arange(1, len(df_tampil) + 1)
        df_tampil.index.name = 'No.'
        st.dataframe(df_tampil, use_container_width=True)
        st.success(f"✅ Data Dummy aktif. Total kandidat: **{len(df_tampil)}** orang.")

    elif sumber_data == "Input Manual Terbuka":
        st.info("✏️ Edit tabel di bawah ini. Tekan Enter setelah mengubah nilai.")
        df_edit = st.session_state.df.copy()
        df_edit.index = np.arange(1, len(df_edit) + 1)
        df_edit.index.name = 'No.'

        updated_df = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)
        st.session_state.df = updated_df.reset_index(drop=True)

    st.markdown("---")
    st.session_state.kuota = st.number_input(
        "🎯 Tentukan Kuota Penerima Bantuan:",
        min_value=1,
        max_value=max(1, len(st.session_state.df)),
        value=min(st.session_state.kuota, max(1, len(st.session_state.df))),
        help="Jumlah kandidat teratas yang akan ditetapkan sebagai penerima bantuan."
    )


# ==========================================
# HALAMAN 2 & 3: PANEL PREFERENSI DM
# ==========================================
def halaman_panel_preferensi(judul: str, metode: str, state_key: str):
    """Fungsi dinamis untuk pengaturan bobot DM1 dan DM2."""
    st.title(judul)
    st.markdown(
        f"Silakan atur bobot tingkat kepentingan untuk setiap kriteria. "
        f"Sistem menggunakan metode **{metode}**."
    )

    col_kiri, col_kanan = st.columns([2, 1])

    with col_kiri:
        st.subheader("⚙️ Atur Slider Bobot Mentah")
        bobot_saat_ini = st.session_state[state_key]

        for i, nama_kriteria in enumerate(KRITERIA_COLS):
            bobot_saat_ini[i] = st.slider(
                label=nama_kriteria,
                min_value=0.0,
                max_value=1.0,
                value=float(bobot_saat_ini[i]),
                step=0.01,
                key=f"{state_key}_slider_{i}"
            )
        st.session_state[state_key] = bobot_saat_ini

    with col_kanan:
        st.subheader("📊 Bobot Aktif (Normalisasi)")
        total_bobot = np.sum(st.session_state[state_key])
        if total_bobot > 0:
            w_norm = np.array(st.session_state[state_key]) / total_bobot
        else:
            w_norm = np.ones(len(KRITERIA_COLS)) / len(KRITERIA_COLS)

        df_bobot = pd.DataFrame({
            'Kriteria': KRITERIA_COLS,
            'Bobot Normalisasi': np.round(w_norm, 4)
        })
        df_bobot.index = np.arange(1, len(df_bobot) + 1)
        df_bobot.index.name = 'No.'
        st.dataframe(df_bobot, use_container_width=True)
        st.metric("Total Bobot", f"{round(w_norm.sum() * 100, 1)}%")


# ==========================================
# HALAMAN 4: PAPAN HASIL AGREGASI
# ==========================================
def halaman_papan_hasil():
    """Halaman hasil agregasi akhir tanpa fitur ekspor/cetak."""
    st.title("🏆 Papan Hasil Agregasi GDSS")

    df = st.session_state.df.copy()
    if df.empty:
        st.error("⚠️ **Data Kandidat kosong.** Isi data di halaman **Kelola Data Kandidat**.")
        return

    missing_cols = [col for col in KRITERIA_COLS if col not in df.columns]
    if missing_cols:
        st.error(f"⚠️ **Data tidak valid.** Kolom hilang: `{'`, `'.join(missing_cols)}`")
        return

    # --- Proses Kalkulasi ---
    sum_w1 = np.sum(st.session_state.w1)
    sum_w2 = np.sum(st.session_state.w2)
    w1_norm = (np.array(st.session_state.w1) / sum_w1 if sum_w1 > 0 else np.ones(len(KRITERIA_COLS)) / len(KRITERIA_COLS))
    w2_norm = (np.array(st.session_state.w2) / sum_w2 if sum_w2 > 0 else np.ones(len(KRITERIA_COLS)) / len(KRITERIA_COLS))
    
    KUOTA = min(st.session_state.kuota, len(df))
    matrix = df[KRITERIA_COLS].values.astype(float)

    # 1. SAW (DM1)
    _, skor_saw = hitung_SAW(matrix, w1_norm, TIPE_BENEFIT)
    df_saw = df[['Nama']].copy()
    df_saw['Skor_SAW'] = np.round(skor_saw, 4)
    df_saw['Rank_SAW'] = df_saw['Skor_SAW'].rank(ascending=False).astype(int)

    # 2. TOPSIS (DM2)
    *_, skor_topsis = hitung_TOPSIS(matrix, w2_norm, TIPE_BENEFIT)
    df_topsis = df[['Nama']].copy()
    df_topsis['Skor_TOPSIS'] = np.round(skor_topsis, 4)
    df_topsis['Rank_TOPSIS'] = df_topsis['Skor_TOPSIS'].rank(ascending=False).astype(int)

    # 3. BORDA (Agregasi)
    df_borda = df[['Nama', 'Desa']].copy()
    df_borda['Rank_SAW'] = df_saw['Rank_SAW'].values
    df_borda['Rank_TOPSIS'] = df_topsis['Rank_TOPSIS'].values
    _, _, b_total = hitung_BORDA(df_borda['Rank_SAW'], df_borda['Rank_TOPSIS'], len(df))
    df_borda['Total_Borda'] = b_total
    df_borda['Rank_Final'] = df_borda['Total_Borda'].rank(ascending=False).astype(int)
    
    df_borda = df_borda.sort_values('Rank_Final').reset_index(drop=True)
    top_kandidat = df_borda.head(KUOTA)

    # --- Output Tabel ---
    st.subheader(f"🥇 Top {KUOTA} Penerima Bantuan Sosial Prioritas")
    
    top_tampil = top_kandidat.copy()
    top_tampil.insert(0, 'No.', np.arange(1, len(top_tampil) + 1))
    top_tampil = top_tampil.reset_index(drop=True).set_index('No.')
    st.table(top_tampil)

    with st.expander("🔍 Lihat Peringkat Detail (SAW & TOPSIS)"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**DM1 — SAW (Dinsos)**")
            st.dataframe(df_saw.sort_values('Rank_SAW'), hide_index=True, use_container_width=True)
        with col2:
            st.markdown("**DM2 — TOPSIS (Camat)**")
            st.dataframe(df_topsis.sort_values('Rank_TOPSIS'), hide_index=True, use_container_width=True)

    # --- Visualisasi ---
    st.markdown("---")
    st.header("📊 Analisis Visualisasi GDSS")

    # Plot 1: Skor Perbandingan
    st.subheader("1. Perbandingan Skor Normalisasi (SAW vs TOPSIS)")
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    nama_sorted = df_borda['Nama'].values
    skor_saw_v = df_saw.set_index('Nama').loc[nama_sorted, 'Skor_SAW'].values
    skor_topsis_v = df_topsis.set_index('Nama').loc[nama_sorted, 'Skor_TOPSIS'].values
    x = np.arange(len(nama_sorted))
    ax1.bar(x - 0.17, skor_saw_v, 0.35, label='SAW', color='steelblue')
    ax1.bar(x + 0.17, skor_topsis_v, 0.35, label='TOPSIS', color='darkorange')
    ax1.set_xticks(x)
    ax1.set_xticklabels([n.split()[0] for n in nama_sorted], rotation=45)
    ax1.legend()
    st.pyplot(fig1)

    # Plot 2: Total Borda
    st.subheader("2. Total Skor Borda Kandidat")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    colors = ['gold' if i < KUOTA else 'lightgray' for i in range(len(df_borda))]
    ax2.barh(range(len(df_borda)), df_borda['Total_Borda'].values, color=colors)
    ax2.set_yticks(range(len(df_borda)))
    ax2.set_yticklabels([f"{r}. {n}" for r, n in zip(df_borda['Rank_Final'], df_borda['Nama'])])
    ax2.invert_yaxis()
    st.pyplot(fig2)

    # Plot 3: Selisih Rank
    st.subheader("3. Selisih Peringkat SAW vs TOPSIS")
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    df_borda['Delta_Rank'] = (df_borda['Rank_SAW'] - df_borda['Rank_TOPSIS']).abs()
    df_delta = df_borda.sort_values('Delta_Rank', ascending=False)
    ax3.barh(range(len(df_delta)), df_delta['Delta_Rank'].values, color='tomato')
    ax3.set_yticks(range(len(df_delta)))
    ax3.set_yticklabels(df_delta['Nama'])
    ax3.invert_yaxis()
    ax3.axvline(x=2, color='black', linestyle='--', alpha=0.5, label='Batas Diskusi (>2)')
    ax3.legend()
    st.pyplot(fig3)


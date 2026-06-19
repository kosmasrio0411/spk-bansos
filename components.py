"""
components.py — Fungsi Halaman GDSS Bansos (Socket.IO Edition)
================================================================
Integrasi WebSocket real-time menggunakan dua lapisan sinkronisasi:

  Lapisan 1 — Python (reliable):
    - requests.post → socket server saat tombol diklik (push weights)
    - requests.get  → socket server setiap rerun papan hasil (pull weights)
    - st_autorefresh(2000ms) → trigger Python rerun periodik

  Lapisan 2 — JavaScript (instant):
    - Socket.IO JS client di panel: emit 'update_weights' ke server
    - Socket.IO JS client di papan: listen 'broadcast_weights' → notifikasi visual

  Kedua lapisan bekerja secara independen — jika salah satu gagal,
  yang lain tetap berfungsi sebagai fallback.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st
from streamlit_autorefresh import st_autorefresh

try:
    import requests as _req
    _HTTP_AVAILABLE = True
except ImportError:
    _HTTP_AVAILABLE = False

from logic import (
    KRITERIA_COLS,
    TIPE_BENEFIT,
    hitung_SAW,
    hitung_TOPSIS,
    hitung_BORDA,
)
from auth import init_session_state as _ensure_state

matplotlib.use("Agg")


# ==============================================================================
# KONFIGURASI SOCKET SERVER URL
# ==============================================================================
# Ganti nilai default di bawah dengan URL Render Socket Server Anda,
# atau atur melalui environment variable:
#   Windows  : set SOCKET_URL=https://nama-socket-kamu.onrender.com
#   Linux/Mac: export SOCKET_URL=https://nama-socket-kamu.onrender.com
#   Streamlit Cloud: tambahkan di Secrets → SOCKET_URL = "https://..."

SOCKET_URL = os.environ.get(
    "SOCKET_URL",
    "http://localhost:5000"          # ← Ganti dengan URL Render setelah deploy
).rstrip("/")


# ==============================================================================
# HELPER: Komunikasi ke Socket Server (Python-side)
# ==============================================================================

def _push_weights_to_server(state_key: str) -> tuple[bool, str]:
    """
    Kirim bobot terbaru dari st.session_state ke socket server via REST POST.
    Socket server akan langsung broadcast ke semua tab aktif.

    Args:
        state_key: "w1" (Dinsos) atau "w2" (Camat)

    Returns:
        (berhasil: bool, pesan: str)
    """
    if not _HTTP_AVAILABLE:
        return False, "Library `requests` tidak tersedia."

    # Konversi numpy array / list ke list float biasa (JSON-safe)
    weights_list = [float(w) for w in st.session_state[state_key]]

    try:
        resp = _req.post(
            f"{SOCKET_URL}/weights",
            json={"key": state_key, "weights": weights_list},
            timeout=3,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code == 200:
            return True, f"Dikirim ke server ({SOCKET_URL})"
        return False, f"Server menolak: HTTP {resp.status_code} — {resp.text[:80]}"

    except _req.exceptions.ConnectionError:
        return False, f"Koneksi ditolak. Socket server tidak berjalan di {SOCKET_URL}"
    except _req.exceptions.Timeout:
        return False, "Timeout 3 detik — socket server tidak merespons."
    except Exception as exc:
        return False, f"Error tidak terduga: {exc}"


def _sync_weights_from_server() -> tuple[bool, str]:
    """
    Ambil bobot terbaru dari socket server via REST GET dan update session_state.
    Dipanggil di awal setiap render Papan Hasil untuk mendapatkan bobot real-time.

    Returns:
        (berhasil: bool, pesan: str)
    """
    if not _HTTP_AVAILABLE:
        return False, "Library `requests` tidak tersedia."

    try:
        resp = _req.get(f"{SOCKET_URL}/weights", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            updated = []
            for key in ("w1", "w2"):
                val = data.get(key)
                if isinstance(val, list) and len(val) == 9:
                    st.session_state[key] = [float(v) for v in val]
                    updated.append(key)
            if updated:
                return True, f"Sinkron OK ({', '.join(updated)})"
            return False, "Data dari server tidak valid."
        return False, f"HTTP {resp.status_code}"

    except _req.exceptions.ConnectionError:
        return False, "Socket server tidak tersedia."
    except _req.exceptions.Timeout:
        return False, "Timeout 2 detik."
    except Exception as exc:
        return False, f"Error: {exc}"


# ==============================================================================
# HELPER: Socket.IO JavaScript Components
# ==============================================================================

def _render_socket_emit(state_key: str, weights_list: list) -> None:
    """
    Sisipkan komponen HTML kecil yang mengirim bobot ke socket server
    via JavaScript Socket.IO client (lapisan tambahan di atas Python POST).

    Komponen ini hanya dirender setelah tombol diklik, bukan setiap render.
    """
    weights_json = json.dumps(weights_list)   # Serialisasi aman untuk JavaScript

    html = f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"
          crossorigin="anonymous"></script>
</head>
<body style="margin:0;padding:6px 10px;background:#f0fdf4;
             border-left:3px solid #22c55e;border-radius:4px;">
  <span id="msg" style="font-size:11px;font-family:monospace;color:#166534;">
    ⏳ Menghubungkan ke Socket Server via JavaScript...
  </span>
  <script>
  (function() {{
    var SOCKET_URL = "{SOCKET_URL}";
    var payload    = {{key: "{state_key}", weights: {weights_json}}};
    var msg        = document.getElementById('msg');

    var socket = io(SOCKET_URL, {{
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 3,
      timeout: 5000,
      forceNew: true,
    }});

    socket.on('connect', function() {{
      msg.innerHTML = '⚡ Terhubung! Mengirim bobot <b>{state_key.upper()}</b> via Socket.IO...';
      socket.emit('update_weights', payload);
      setTimeout(function() {{
        msg.innerHTML = '✅ Bobot <b>{state_key.upper()}</b> berhasil dikirim via JS Socket. ' +
                        'Semua tab aktif akan mendapat notifikasi instan.';
        socket.disconnect();
      }}, 700);
    }});

    socket.on('connect_error', function(err) {{
      msg.innerHTML = '⚠️ JS Socket tidak terhubung (sudah dikirim via REST API). ' +
                      'Error: ' + err.message;
      msg.style.color = '#92400e';
    }});
  }})();
  </script>
</body>
</html>"""

    st.components.v1.html(html, height=36)


def _render_socket_listener() -> None:
    """
    Listener JS yang memicu perubahan nilai pada elemen HTML Streamlit secara langsung.
    Ketika ada broadcast, ia menyuntikkan teks timestamp ke text_input tersembunyi
    dan langsung memicu instan rerun dari sisi frontend.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js" crossorigin="anonymous"></script>
  <style>
    body {{
      margin: 0; padding: 5px 10px;
      background: #0f172a; border-radius: 4px;
      font-family: 'Courier New', monospace; font-size: 11px;
    }}
    #status {{ color: #4ade80; }}
  </style>
</head>
<body>
  <div id="status">📡 Menghubungkan ke Socket Server...</div>
  <script>
  (function() {{
    var SOCKET_URL = "{SOCKET_URL}";
    var el = document.getElementById('status');

    var socket = io(SOCKET_URL, {{
      transports: ['websocket', 'polling'],
      reconnectionAttempts: 5
    }});

    socket.on('connect', function() {{
      el.innerHTML = '🟢 Terhubung | Memantau perubahan bobot DM1 &amp; DM2...';
    }});

    socket.on('broadcast_weights', function(data) {{
      var ts = new Date().toLocaleTimeString('id-ID');
      el.style.color = '#facc15';
      el.innerHTML = '⚡ UPDATE DITERIMA: [' + data.key.toUpperCase() + '] pukul ' + ts;

      // TRICK UTAMA: Cari elemen text_input milik Streamlit di window parent dan isi nilainya
      // Ini akan memaksa Streamlit mendeteksi perubahan input secara instan tanpa membuat blur seluruh layar
      setTimeout(function() {{
        window.parent.postMessage({{
          type: 'streamlit:setComponentValue',
          value: JSON.stringify({{ ts: Date.now(), key: data.key }}),
        }}, '*');
        
        // Kirim event klik atau enter tiruan ke dokumen utama jika diperlukan
        var inputs = window.parent.document.querySelectorAll('input');
        inputs.forEach(function(input) {{
            if(input.ariaLabel === "socket_trigger_input") {{
                input.value = data.key + "_" + Date.now();
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }});
      }}, 100);
    }});
  }})();
  </script>
</body>
</html>"""

    st.components.v1.html(html, height=42)
# ==============================================================================
# HALAMAN 1: KELOLA DATA KANDIDAT
# ==============================================================================

def halaman_kelola_data():
    """Halaman Admin/Operator untuk mengelola data kandidat penerima Bansos."""
    _ensure_state()

    st.title("📋 Kelola Data Kandidat Bansos")
    st.markdown(
        "Halaman ini diakses oleh **Admin Desa/Operator** "
        "untuk memasukkan data warga calon penerima bantuan sosial."
    )

    sumber_data = st.radio(
        "Pilih metode input data:",
        ["Data Dummy Bawaan", "Input Manual Terbuka"],
        horizontal=True,
    )

    if sumber_data == "Data Dummy Bawaan":
        from auth import _get_dummy_data
        st.session_state.df = _get_dummy_data()
        df_tampil = st.session_state.df.copy()
        df_tampil.index = np.arange(1, len(df_tampil) + 1)
        df_tampil.index.name = "No."
        st.dataframe(df_tampil, use_container_width=True)
        st.success(f"✅ Data Dummy aktif. Total kandidat: **{len(df_tampil)}** orang.")

    elif sumber_data == "Input Manual Terbuka":
        st.info("✏️ Edit tabel di bawah ini. Tekan Enter setelah mengubah nilai.")
        df_edit = st.session_state.df.copy()
        df_edit.index = np.arange(1, len(df_edit) + 1)
        df_edit.index.name = "No."
        updated_df = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)
        st.session_state.df = updated_df.reset_index(drop=True)

    st.markdown("---")
    st.session_state.kuota = st.number_input(
        "🎯 Tentukan Kuota Penerima Bantuan:",
        min_value=1,
        max_value=max(1, len(st.session_state.df)),
        value=min(st.session_state.kuota, max(1, len(st.session_state.df))),
        help="Jumlah kandidat teratas yang akan ditetapkan sebagai penerima bantuan.",
    )


# ==============================================================================
# HALAMAN 2 & 3: PANEL PREFERENSI DM
# ==============================================================================

def halaman_panel_preferensi(judul: str, metode: str, state_key: str):
    """
    Panel pengaturan bobot preferensi untuk satu Decision Maker.

    Saat tombol '🚀 Kirim & Sinkronkan Bobot' diklik:
      1. st.session_state[state_key] diperbarui dengan nilai slider terkini.
      2. Python POST ke socket server REST → server broadcast ke semua tab.
      3. JavaScript Socket.IO emit sebagai lapisan konfirmasi tambahan.
    """
    _ensure_state()

    st.title(judul)
    st.markdown(
        f"Silakan atur bobot tingkat kepentingan untuk setiap kriteria. "
        f"Sistem menggunakan metode **{metode}**."
    )

    # ── Info Socket Server ─────────────────────────────────────────────────
    with st.expander("⚙️ Konfigurasi Socket Server", expanded=False):
        st.code(f"SOCKET_URL = {SOCKET_URL}", language="text")
        st.caption(
            "Ubah URL via environment variable: "
            "`export SOCKET_URL=https://nama.onrender.com` "
            "sebelum menjalankan Streamlit."
        )

    col_kiri, col_kanan = st.columns([2, 1])

    # ── Kolom kiri: 9 Slider Kriteria ─────────────────────────────────────
    with col_kiri:
        st.subheader("⚙️ Atur Slider Bobot Mentah (9 Kriteria)")
        bobot_saat_ini = list(st.session_state[state_key])   # shallow copy list

        for i, nama_kriteria in enumerate(KRITERIA_COLS):
            bobot_saat_ini[i] = st.slider(
                label=nama_kriteria,
                min_value=0.0,
                max_value=1.0,
                value=float(bobot_saat_ini[i]),
                step=0.01,
                key=f"{state_key}_slider_{i}",
            )

        st.session_state[state_key] = bobot_saat_ini

    # ── Kolom kanan: Normalisasi bobot ────────────────────────────────────
    with col_kanan:
        st.subheader("📊 Bobot Aktif (Normalisasi)")
        total_bobot = np.sum(bobot_saat_ini)
        w_norm = (
            np.array(bobot_saat_ini) / total_bobot
            if total_bobot > 0
            else np.ones(len(KRITERIA_COLS)) / len(KRITERIA_COLS)
        )

        df_bobot = pd.DataFrame({
            "Kriteria":          KRITERIA_COLS,
            "Bobot Normalisasi": np.round(w_norm, 4),
        })
        df_bobot.index = np.arange(1, len(df_bobot) + 1)
        df_bobot.index.name = "No."
        st.dataframe(df_bobot, use_container_width=True)
        st.metric("Total Bobot", f"{round(w_norm.sum() * 100, 1)}%")

    # ── Tombol kirim & sinkronkan ──────────────────────────────────────────
    st.markdown(" ")
    if st.button(
        "🚀 Kirim & Sinkronkan Bobot",
        type="primary",
        use_container_width=True,
        key=f"btn_send_{state_key}",
    ):
        # Konversi ke list float biasa (aman untuk JSON / socket transfer)
        weights_list = [float(w) for w in bobot_saat_ini]

        # ── Lapisan 1: Python REST POST ke socket server ──────────────────
        ok, msg = _push_weights_to_server(state_key)

        if ok:
            st.success(
                f"✅ **Bobot {state_key.upper()} berhasil dikirim ke socket server!**\n\n"
                f"📍 {msg}\n\n"
                f"Papan Hasil Agregasi di semua tab akan memperbarui data dalam ~2 detik."
            )
        else:
            st.warning(
                f"⚠️ **REST API gagal:** {msg}\n\n"
                f"Bobot tersimpan di sesi lokal Anda. "
                f"JavaScript Socket.IO akan mencoba mengirim langsung..."
            )

        # ── Lapisan 2: JavaScript Socket.IO emit (konfirmasi visual) ─────
        _render_socket_emit(state_key, weights_list)


# ==============================================================================
# HALAMAN 4: PAPAN HASIL AGREGASI (REAL-TIME via Fragment - Bebas Blurry)
# ==============================================================================

def halaman_papan_hasil():
    """
    Papan hasil agregasi GDSS dengan arsitektur Hybrid Fragment.
    Kerangka halaman tetap diam (tidak blur/abu-abu), sementara area kalkulasi 
    dan grafik ter-refresh secara real-time mengecek socket server.
    """
    _ensure_state()

    st.title("🏆 Papan Hasil Agregasi GDSS (Real-time)")
    
    # Render listener di luar fragment agar koneksi socket IO di frontend persisten
    _render_socket_listener()
    
    st.markdown("---")

    # Memanggil kontainer fragment utama
    _render_konten_papan_lengkap()


@st.fragment(run_every=5)
def _render_konten_papan_lengkap():
    """
    Fungsi internal fragment yang memuat seluruh logika perhitungan SPK,
    tabel lengkap, dan 3 plot visualisasi.
    """
    # ── Header bar internal fragment ───────────────────────────────────────
    hdr1, hdr2 = st.columns([5, 1])
    with hdr1:
        st.caption(
            "🔄 Sinkronisasi otomatis setiap **2 detik** via Fragment & Socket Server. "
            "Perubahan bobot dari DM1/DM2 di tab manapun langsung tercermin di bawah."
        )
    with hdr2:
        # Menggunakan timestamp sebagai indikator refresh yang halus
        st.caption(f"⏱️ Live")

    # ── Pull bobot terbaru dari socket server ──────────────────────────────
    server_ok, server_msg = _sync_weights_from_server()

    scol1, scol2 = st.columns([3, 2])
    with scol1:
        if server_ok:
            st.success(f"🟢 Socket Server OK — {server_msg}")
        else:
            st.warning(f"⚠️ Menggunakan data lokal — {server_msg}")
    with scol2:
        st.code(SOCKET_URL, language="text")

    st.markdown("---")

    # ── Validasi data kandidat ─────────────────────────────────────────────
    df = st.session_state.df.copy()
    if df.empty:
        st.error("⚠️ **Data Kandidat kosong.** Isi data di halaman **Kelola Data Kandidat**.")
        return

    missing_cols = [col for col in KRITERIA_COLS if col not in df.columns]
    if missing_cols:
        st.error(f"⚠️ **Data tidak valid.** Kolom hilang: `{'`, `'.join(missing_cols)}`")
        return

    # ── Normalisasi bobot (handle edge case total = 0) ─────────────────────
    raw_w1 = np.array(st.session_state.w1, dtype=float)
    raw_w2 = np.array(st.session_state.w2, dtype=float)
    fallback = np.ones(len(KRITERIA_COLS)) / len(KRITERIA_COLS)

    w1_norm = raw_w1 / raw_w1.sum() if raw_w1.sum() > 0 else fallback
    w2_norm = raw_w2 / raw_w2.sum() if raw_w2.sum() > 0 else fallback

    KUOTA  = min(st.session_state.kuota, len(df))
    matrix = df[KRITERIA_COLS].values.astype(float)

    # ── Tampilkan bobot aktif kedua DM ────────────────────────────────────
    st.subheader("🎛️ Bobot Aktif Kedua DM (dari Socket Server)")
    bc1, bc2 = st.columns(2)
    with bc1:
        st.markdown("**👥 DM1 — Kepala Dinsos (SAW)**")
        df_w1_disp = pd.DataFrame({
            "Kriteria":     KRITERIA_COLS,
            "Bobot Norm.":  np.round(w1_norm, 4),
        })
        df_w1_disp.index = np.arange(1, len(df_w1_disp) + 1)
        st.dataframe(df_w1_disp, use_container_width=True, hide_index=False)
    with bc2:
        st.markdown("**👤 DM2 — Camat (TOPSIS)**")
        df_w2_disp = pd.DataFrame({
            "Kriteria":     KRITERIA_COLS,
            "Bobot Norm.":  np.round(w2_norm, 4),
        })
        df_w2_disp.index = np.arange(1, len(df_w2_disp) + 1)
        st.dataframe(df_w2_disp, use_container_width=True, hide_index=False)

    st.markdown("---")

    # ── 1. SAW (DM1) ──────────────────────────────────────────────────────
    _, skor_saw = hitung_SAW(matrix, w1_norm, TIPE_BENEFIT)
    df_saw = df[["Nama"]].copy()
    df_saw["Skor_SAW"]  = np.round(skor_saw, 4)
    df_saw["Rank_SAW"]  = df_saw["Skor_SAW"].rank(ascending=False).astype(int)

    # ── 2. TOPSIS (DM2) ────────────────────────────────────────────────────
    *_, skor_topsis = hitung_TOPSIS(matrix, w2_norm, TIPE_BENEFIT)
    df_topsis = df[["Nama"]].copy()
    df_topsis["Skor_TOPSIS"]  = np.round(skor_topsis, 4)
    df_topsis["Rank_TOPSIS"]  = df_topsis["Skor_TOPSIS"].rank(ascending=False).astype(int)

    # ── 3. BORDA (Agregasi) ────────────────────────────────────────────────
    df_borda = df[["Nama", "Desa"]].copy()
    df_borda["Rank_SAW"]    = df_saw["Rank_SAW"].values
    df_borda["Rank_TOPSIS"] = df_topsis["Rank_TOPSIS"].values
    _, _, b_total = hitung_BORDA(
        df_borda["Rank_SAW"], df_borda["Rank_TOPSIS"], len(df)
    )
    df_borda["Total_Borda"] = b_total
    df_borda["Rank_Final"]  = df_borda["Total_Borda"].rank(ascending=False).astype(int)
    df_borda = df_borda.sort_values("Rank_Final").reset_index(drop=True)
    top_kandidat = df_borda.head(KUOTA)

    # ── Tabel ranking final ────────────────────────────────────────────────
    st.subheader(f"🥇 Top {KUOTA} Penerima Bantuan Sosial Prioritas")
    top_tampil = top_kandidat.copy()
    top_tampil.insert(0, "No.", np.arange(1, len(top_tampil) + 1))
    top_tampil = top_tampil.reset_index(drop=True).set_index("No.")
    st.table(top_tampil)

    with st.expander("🔍 Lihat Peringkat Detail (SAW & TOPSIS)"):
        dc1, dc2 = st.columns(2)
        with dc1:
            st.markdown("**DM1 — SAW (Dinsos)**")
            st.dataframe(
                df_saw.sort_values("Rank_SAW"),
                hide_index=True, use_container_width=True,
            )
        with dc2:
            st.markdown("**DM2 — TOPSIS (Camat)**")
            st.dataframe(
                df_topsis.sort_values("Rank_TOPSIS"),
                hide_index=True, use_container_width=True,
            )

    # ── Visualisasi: 3 Plot Matplotlib ────────────────────────────────────
    st.markdown("---")
    st.header("📊 Analisis Visualisasi GDSS (Live)")

    nama_sorted   = df_borda["Nama"].values
    skor_saw_v    = df_saw.set_index("Nama").loc[nama_sorted, "Skor_SAW"].values
    skor_topsis_v = df_topsis.set_index("Nama").loc[nama_sorted, "Skor_TOPSIS"].values

    # ── Plot 1: SAW vs TOPSIS ─────────────────────────────────────────────
    st.subheader("1. Perbandingan Skor Normalisasi (SAW vs TOPSIS)")
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    x = np.arange(len(nama_sorted))
    ax1.bar(x - 0.17, skor_saw_v,    0.35, label="SAW (DM1)",    color="steelblue",  alpha=0.85)
    ax1.bar(x + 0.17, skor_topsis_v, 0.35, label="TOPSIS (DM2)", color="darkorange", alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels([n.split()[0] for n in nama_sorted], rotation=45, fontsize=8)
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_title("Skor SAW vs TOPSIS — Bobot Live dari Socket Server")
    plt.tight_layout()
    st.pyplot(fig1)
    plt.close(fig1)

    # ── Plot 2: Total Borda ────────────────────────────────────────────────
    st.subheader("2. Total Skor Borda Kandidat")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    colors = ["gold" if i < KUOTA else "lightgray" for i in range(len(df_borda))]
    ax2.barh(range(len(df_borda)), df_borda["Total_Borda"].values, color=colors)
    ax2.set_yticks(range(len(df_borda)))
    ax2.set_yticklabels(
        [f"{r}. {n}" for r, n in zip(df_borda["Rank_Final"], df_borda["Nama"])],
        fontsize=8,
    )
    ax2.invert_yaxis()
    ax2.grid(axis="x", alpha=0.3)
    legend_patches = [
        mpatches.Patch(color="gold",      label=f"Top {KUOTA} Penerima"),
        mpatches.Patch(color="lightgray", label="Belum Lolos"),
    ]
    ax2.legend(handles=legend_patches)
    ax2.set_title("Peringkat Borda — Agregasi Keputusan DM1 + DM2")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # ── Plot 3: Selisih Rank (Konsensus DM) ───────────────────────────────
    st.subheader("3. Selisih Peringkat SAW vs TOPSIS (Indikator Konsensus)")
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    df_borda_plot = df_borda.copy()
    df_borda_plot["Delta_Rank"] = (
        df_borda_plot["Rank_SAW"] - df_borda_plot["Rank_TOPSIS"]
    ).abs()
    df_delta = df_borda_plot.sort_values("Delta_Rank", ascending=False)
    bar_colors = [
        "tomato" if d > 2 else "mediumseagreen"
        for d in df_delta["Delta_Rank"].values
    ]
    ax3.barh(range(len(df_delta)), df_delta["Delta_Rank"].values, color=bar_colors)
    ax3.set_yticks(range(len(df_delta)))
    ax3.set_yticklabels(df_delta["Nama"], fontsize=8)
    ax3.invert_yaxis()
    ax3.axvline(x=2, color="black", linestyle="--", alpha=0.5, label="Batas Diskusi (>2)")
    ax3.legend()
    ax3.grid(axis="x", alpha=0.3)
    ax3.set_title("Selisih Rank (Merah = Perlu Diskusi | Hijau = Konsensus Tercapai)")
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)
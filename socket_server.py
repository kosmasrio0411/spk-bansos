"""
socket_server.py — Backend WebSocket GDSS Bansos
==================================================
Menjalankan Flask + Flask-SocketIO sebagai server WebSocket terpisah.
Kompatibel untuk deploy di Render sebagai Web Service independen.

Deployment di Render:
    Build Command  : pip install -r requirements.txt
    Start Command  : gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --bind 0.0.0.0:$PORT socket_server:app
    Environment Var: PORT (diisi otomatis Render), SECRET_KEY (opsional)

Jalankan lokal:
    python socket_server.py
"""

import os
import logging

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

# ==============================================================================
# LOGGING
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("gdss_socket")


# ==============================================================================
# FLASK + SOCKET.IO SETUP
# ==============================================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gdss-bansos-secret-2024")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",       # Buka CORS untuk semua domain (Render + Streamlit Cloud)
    async_mode="gevent",            # Wajib gevent untuk WebSocket di production
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1_000_000,
)


# ==============================================================================
# GLOBAL STATE — Bobot Kriteria Kedua DM (9 Kriteria sesuai logic.py)
# ==============================================================================
# Urutan sesuai KRITERIA_COLS di logic.py:
#   C1_KK_Serumah, C2_Pendidikan, C3_Anggota_Kel, C4_Masih_Sekolah,
#   C5_Pengeluaran, C6_Penghasilan, C7_Kondisi_Rumah,
#   C8_Tanggungan_Khusus, C9_Jarak_Fasilitas

_server_weights: dict = {
    "w1": [0.05, 0.10, 0.05, 0.08, 0.25, 0.27, 0.08, 0.07, 0.05],  # DM1 Dinsos (SAW)
    "w2": [0.10, 0.12, 0.10, 0.15, 0.10, 0.11, 0.15, 0.12, 0.05],  # DM2 Camat (TOPSIS)
}

_VALID_KEYS = ("w1", "w2")


# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.route("/", methods=["GET"])
def index():
    """Root endpoint — identifikasi service."""
    return jsonify({
        "service": "GDSS Bansos WebSocket Server",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "GET  /health":  "Uptime check untuk Render",
            "GET  /weights": "Ambil bobot terkini kedua DM",
            "POST /weights": "Kirim bobot baru (payload: {key, weights})",
        },
    })


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    Digunakan oleh Render uptime monitoring agar service tidak sleep.
    """
    return jsonify({"status": "ok", "service": "GDSS Bansos Socket Server"})


@app.route("/weights", methods=["GET"])
def get_weights():
    """
    Mengembalikan snapshot bobot terkini dari kedua DM.

    Dipanggil oleh Streamlit (Python) via requests.get() di setiap
    rerun halaman Papan Hasil Agregasi untuk mendapatkan bobot terbaru.

    Response:
        {"w1": [float × 9], "w2": [float × 9]}
    """
    return jsonify({
        "w1": _server_weights["w1"],
        "w2": _server_weights["w2"],
    })


@app.route("/weights", methods=["POST"])
def post_weights():
    """
    Menerima bobot baru dari Streamlit via requests.post().
    Memperbarui state global server dan broadcast ke seluruh Socket.IO client.

    Expected JSON payload:
        {"key": "w1" | "w2", "weights": [float × 9]}

    Response:
        {"status": "ok", "key": "w1", "weights": [...]}
    """
    payload = request.get_json(force=True, silent=True)

    # Validasi payload
    if not payload:
        return jsonify({"error": "Payload JSON tidak valid atau kosong"}), 400

    key     = payload.get("key")
    weights = payload.get("weights")

    if key not in _VALID_KEYS:
        return jsonify({"error": f'key harus "w1" atau "w2", bukan "{key}"'}), 400
    if not isinstance(weights, list) or len(weights) != 9:
        return jsonify({"error": "weights harus berupa list 9 float"}), 400

    # Update global state (konversi aman ke float)
    _server_weights[key] = [float(w) for w in weights]
    log.info(f"[REST POST] {key} diperbarui: {[round(w, 3) for w in _server_weights[key]]}")

    # Broadcast ke SEMUA Socket.IO client yang terhubung
    socketio.emit("broadcast_weights", {
        "key":     key,
        "weights": _server_weights[key],
        "source":  "rest",
    })

    return jsonify({
        "status":  "ok",
        "key":     key,
        "weights": _server_weights[key],
    })


# ==============================================================================
# SOCKET.IO EVENTS
# ==============================================================================

@socketio.on("connect")
def on_connect():
    """
    Client baru terhubung.
    Kirim snapshot bobot terkini sebagai inisialisasi awal.
    """
    sid = request.sid
    log.info(f"[CONNECT ] Client terhubung  → {sid}")

    # Inisialisasi: kirim state terkini ke client yang baru saja connect
    emit("init_weights", {
        "w1": _server_weights["w1"],
        "w2": _server_weights["w2"],
    })


@socketio.on("disconnect")
def on_disconnect():
    """Client terputus."""
    log.info(f"[DISCONN ] Client terputus  → {request.sid}")


@socketio.on("update_weights")
def on_update_weights(data):
    """
    Menerima update bobot dari panel preferensi via JavaScript Socket.IO.
    Memperbarui state global dan broadcast ke SEMUA client aktif.

    Expected payload (dari JS):
        {key: "w1" | "w2", weights: [float × 9]}
    """
    if not isinstance(data, dict):
        log.warning(f"[update_weights] Payload bukan dict: {data}")
        return

    key     = data.get("key")
    weights = data.get("weights")

    # Validasi
    if key not in _VALID_KEYS:
        log.warning(f"[update_weights] key tidak valid: {key}")
        return
    if not isinstance(weights, list) or len(weights) == 0:
        log.warning(f"[update_weights] weights tidak valid untuk {key}")
        return

    # Update state global
    _server_weights[key] = [float(w) for w in weights]
    log.info(
        f"[SOCKET  ] {key} diperbarui oleh {request.sid}: "
        f"{[round(w, 3) for w in _server_weights[key]]}"
    )

    # Broadcast ke SEMUA client (termasuk pengirim) dengan broadcast=True
    emit("broadcast_weights", {
        "key":     key,
        "weights": _server_weights[key],
        "source":  "socket",
    }, broadcast=True)


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    log.info("=" * 60)
    log.info("  GDSS Bansos — Socket.IO Server")
    log.info(f"  Host     : 0.0.0.0")
    log.info(f"  Port     : {port}")
    log.info(f"  Async    : {socketio.async_mode}")
    log.info(f"  CORS     : *  (semua origin diizinkan)")
    log.info("=" * 60)
    log.info("Tekan Ctrl+C untuk menghentikan server.")
    log.info("")

    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False,
        log_output=False,
    )

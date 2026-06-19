# 📊 GDSS Seleksi Prioritas Penerima Bantuan Sosial

Aplikasi web interaktif berbasis **Streamlit** untuk Sistem Pendukung Keputusan Berkelompok (*Group Decision Support System* / GDSS). Sistem ini dirancang untuk menyeleksi kandidat penerima bantuan sosial (Bansos) dengan mengakomodasi preferensi dari dua Pengambil Keputusan (*Decision Maker* / DM) yang berbeda.

Aplikasi ini menggunakan kombinasi tiga metode pengambilan keputusan:

1. **SAW (Simple Additive Weighting)**: Digunakan oleh DM1 (Kepala Dinas Sosial).
2. **TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)**: Digunakan oleh DM2 (Camat).
3. **Borda Count**: Digunakan sebagai metode agregasi untuk menggabungkan peringkat dari kedua DM menjadi satu keputusan akhir.

---

## ✨ Fitur Utama

* **Multi-Page Interface**: Antarmuka navigasi modern menggunakan `streamlit-option-menu`.
* **Input Data Fleksibel**: Menyediakan opsi penggunaan data dummy bawaan atau input manual interaktif bergaya *spreadsheet* (*Data Editor*).
* **Panel Preferensi DM Independen**: Masing-masing DM dapat mengatur bobot kriteria secara terpisah menggunakan *slider*, dan sistem akan menormalisasinya otomatis.
* **Agregasi Hasil Otomatis**: Menyajikan *Top N* kandidat terbaik berdasarkan kuota yang ditentukan.
* **Visualisasi & Analisis Lengkap**:
* Grafik perbandingan skor akhir (SAW vs TOPSIS).
* Grafik total skor Borda untuk melihat kandidat yang lolos kuota.
* Analisis selisih peringkat untuk mendeteksi perbedaan pendapat antar DM.
* **Analisis Sensitivitas** untuk melihat pergeseran *Top 3* jika bobot salah satu kriteria (misal: Penghasilan) diubah.



---

## 🛠️ Prasyarat (*Dependencies*)

Pastikan komputer/laptop yang digunakan sudah terinstal **Python** (disarankan versi 3.9 atau lebih baru). Aplikasi ini sekarang menggunakan arsitektur **WebSocket (Socket.IO)** untuk sinkronisasi *real-time* yang mulus antar-tab tanpa perlu me-refresh halaman secara manual.

---

## 🚀 Cara Instalasi dan Menjalankan Aplikasi

Aplikasi ini berjalan dengan dua servis yang saling terhubung: **Socket Server** (sebagai *backend* sinkronisasi) dan **Streamlit App** (sebagai *frontend/client*).

**Langkah 1: Instal Library (Satu kali saja)**
Buka Terminal atau Command Prompt (CMD) di folder proyek ini, lalu instal semua dependensi melalui `requirements.txt`:

```bash
pip install -r requirements.txt
```

*(Tunggu hingga proses instalasi Flask-SocketIO, gevent, Streamlit, dsb selesai)*

**Langkah 2: Jalankan Socket Server (Terminal 1)**
Sistem GDSS membutuhkan server komunikasi agar tab Dinsos dan Camat bisa saling mengirim bobot secara *real-time*. Di terminal pertama, jalankan:

```bash
python socket_server.py
```
*(Biarkan terminal ini tetap terbuka dan berjalan)*

**Langkah 3: Jalankan Aplikasi Streamlit (Terminal 2)**
Buka **terminal baru** (biarkan terminal pertama tetap jalan), arahkan ke folder proyek, dan jalankan:

```bash
streamlit run app.py
```

Aplikasi akan otomatis terbuka di *browser* Anda (biasanya di `http://localhost:8501`).

---

## 🔐 Akun Login Demo

Aplikasi menggunakan sistem autentikasi multi-peran. Gunakan kredensial berikut untuk masuk:

| Peran (*Role*) | Username | Password | Akses Halaman |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | Kelola Data, Papan Hasil |
| **Kepala Dinsos** (DM1) | `dinsos` | `dinsos123` | Panel DM1 (SAW), Papan Hasil |
| **Camat** (DM2) | `camat` | `camat123` | Panel DM2 (TOPSIS), Papan Hasil |

---

## 📂 Struktur Navigasi Aplikasi

Setelah login, pengguna hanya akan melihat halaman sesuai hak aksesnya:

1. **Kelola Data Kandidat**: (Hanya Admin) Tempat menentukan kuota dan mengedit data calon penerima bansos.
2. **Panel DM1 (Dinsos)**: (Hanya Dinsos) Tempat mengatur preferensi bobot dengan slider (SAW). Punya tombol *🚀 Kirim & Sinkronkan Bobot*.
3. **Panel DM2 (Camat)**: (Hanya Camat) Tempat mengatur preferensi bobot dengan slider (TOPSIS). Punya tombol *🚀 Kirim & Sinkronkan Bobot*.
4. **Papan Hasil Agregasi**: (Semua Role) Halaman final yang menampilkan hasil agregasi Borda secara **Live/Real-time**. Jika DM1/DM2 menekan tombol sinkronisasi di tab/komputer mereka, grafik di halaman ini akan *update* secara otomatis tanpa perlu *refresh* browser.
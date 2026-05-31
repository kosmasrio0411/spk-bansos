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

Pastikan komputer/laptop yang digunakan sudah terinstal **Python** (disarankan versi 3.8 atau lebih baru).

---

## 🚀 Cara Instalasi dan Menjalankan Aplikasi

**Langkah 1: Siapkan File Proyek**
Buat folder baru untuk proyek ini, lalu simpan kode sumber aplikasi ke dalam file bernama `app.py`. Buka Terminal atau Command Prompt (CMD) dan arahkan ke folder tersebut.

**Langkah 2: Instal Library**
Jalankan perintah berikut di Terminal/CMD untuk menginstal semua kebutuhan aplikasi secara global:

```bash
pip install streamlit streamlit-option-menu matplotlib

```

*(Tunggu hingga proses unduhan dan instalasi selesai 100%)*

**Langkah 3: Jalankan Aplikasi**
Setelah instalasi selesai, jalankan perintah ini untuk membuka aplikasi:

```bash
streamlit run app.py

```

Aplikasi akan otomatis terbuka di *browser* Anda (biasanya di alamat `http://localhost:8501`).

---

## 📂 Struktur Navigasi Aplikasi

Aplikasi ini dibagi menjadi 4 halaman utama:

1. **Kelola Data Kandidat**: Tempat Admin/Operator menentukan kuota bantuan dan mengedit data calon penerima bansos beserta nilai kriterianya.
2. **Panel DM1 (Dinsos)**: Halaman khusus Kepala Dinas Sosial untuk mengatur preferensi bobot kriterianya (dihitung menggunakan SAW).
3. **Panel DM2 (Camat)**: Halaman khusus Camat untuk mengatur preferensi bobot kriterianya (dihitung menggunakan TOPSIS).
4. **Papan Hasil Agregasi**: Halaman final yang menampilkan hasil agregasi Borda, peringkat individu tiap DM, beserta grafik analisis visual.
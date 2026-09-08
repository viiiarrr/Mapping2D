<div align="center">
  <h1>🗺️ 2D Sensor Mapper</h1>
  <p><strong>A comprehensive real-time 2D mapping system using ESP32, IMU Yaw, and Distance Sensors.</strong></p>
</div>

<br />

| Component | Technologies & Status |
| :--- | :--- |
| **Web Visualization** | ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black) ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white) ![Plotly](https://img.shields.io/badge/Plotly.js-3F4F75?style=flat-square&logo=plotly&logoColor=white) ![GitHub Pages](https://img.shields.io/badge/Deployed-GitHub_Pages-brightgreen?style=flat-square&logo=github) |
| **Server / Data Processing** | ![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python&logoColor=white) ![WebSockets](https://img.shields.io/badge/WebSockets-010101?style=flat-square&logo=socketdotio&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white) ![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=flat-square&logo=python&logoColor=white) |
| **Hardware / Firmware** | ![C++](https://img.shields.io/badge/C++-00599C?style=flat-square&logo=c%2B%2B&logoColor=white) ![PlatformIO](https://img.shields.io/badge/PlatformIO-F6822B?style=flat-square&logo=platformio&logoColor=white) ![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=flat-square&logo=espressif&logoColor=white) |
| **CI / CD Pipeline** | [![Deploy Web Visualisasi](https://img.shields.io/github/actions/workflow/status/viiiarrr/TugasAkhir/deploy-pages.yml?style=flat-square&label=GitHub%20Actions)](https://github.com/viiiarrr/TugasAkhir/actions) ![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square) |
| **Author** | ![viiiarrr](https://img.shields.io/badge/Author-viiiarrr-6366f1?style=flat-square) |

---

## 📌 Tentang Proyek Ini

Sistem ini adalah bagian dari Tugas Akhir yang bertujuan untuk memetakan ruang 2D secara *real-time* menggunakan gabungan sensor jarak (8 arah) dan sensor IMU (Yaw) pada board ESP32. Seluruh pergerakan alat akan ditransmisikan via UDP WiFi ke laptop, lalu diteruskan ke Web Browser untuk dirender dan dianalisa dengan algoritma canggih secara instan.

### ✨ Fitur Utama
- **Real-Time Live Mapping:** Data UDP dari ESP32 langsung dirender ke Web Browser via WebSockets.
- **Advanced Filtering:** Menggunakan EMA (Exponential Moving Average) dan Outlier Filter untuk menstabilkan bacaan sensor.
- **RANSAC Wall Fitting:** Algoritma Split-and-Merge dipadukan dengan RANSAC untuk mendeteksi tembok secara otomatis.
- **Phantom Point Detection:** Mampu mendeteksi dan menandai data anomali (Phantom) yang tidak valid.
- **Web Dashboard:** UI Web yang elegan (Light/White Mode), lengkap dengan parameter tuning, slider putar-ulang (Replay Mode), dan Export PNG.

---

## 📂 Struktur Repositori

```text
TugasAkhir/
├── 📁 src/                 ← Kumpulan kode C++ (Firmware ESP32 via PlatformIO)
├── 📁 python/              ← Kumpulan skrip Python (Server, Receiver, Data Generator)
├── 📁 web-visualisasi/     ← Frontend Web (HTML, CSS, JS, Plotly.js)
├── 📁 Data/                ← Data hasil rekam CSV (disimpan oleh server.py)
├── 📜 platformio.ini       ← Konfigurasi build ESP32
└── 📜 jalankan.bat         ← Auto-runner untuk Live Mode
```

---

## 🚀 Cara Menjalankan

Ada 2 mode utama untuk menggunakan sistem ini: **Live Mode** (Pengambilan Data) dan **Replay Mode** (Presentasi / Lihat Data Lama).

### 1️⃣ Live Mode (Pengambilan Data Real-Time)
Sistem ini menggunakan `server.py` sebagai jembatan antara ESP32 (UDP) dengan Browser (WebSocket).

1. Nyalakan ESP32 Anda dan pastikan terhubung ke jaringan Hotspot Laptop.
2. Di laptop Anda (Windows), *double-click* file **`jalankan.bat`**.
3. Terminal akan otomatis terbuka, dan Browser Anda akan langsung terbuka menampilkan Web Visualisasi.
4. Peta akan mulai tergambar secara Live! Data juga otomatis tersimpan ke folder `Data/`.

> **Melihat Live Data dari HP?**
> Pastikan HP Anda di jaringan WiFi yang sama dengan laptop. Buka browser di HP dan ketik IP laptop Anda (misal: `http://192.168.137.1:8080/web-visualisasi/`).

### 2️⃣ Replay Mode (Lihat Ulang Data)
Anda tidak perlu menyalakan ESP32, dan tidak perlu `jalankan.bat`. Semua hasil rekam CSV bisa diputar ulang di web!

1. Buka link web berikut: **[https://viiiarrr.github.io/TugasAkhir/web-visualisasi/](https://viiiarrr.github.io/TugasAkhir/web-visualisasi/)**
2. Gunakan *Dropdown* "Pilih Percobaan" di sebelah kiri untuk melihat percobaan sebelumnya.
3. Anda juga bisa men- *Drag & Drop* file `koordinat.csv` langsung ke dalam web.
4. Gunakan Slider di bawah layar untuk memutar ulang proses pemetaan dari awal sampai akhir.

---

## 💻 Dependencies

- **Hardware:** ESP32, Sensor IMU (BNO055/MPU6050), 8x Sensor Jarak (VL53L0X / Ultrasonic).
- **Firmware:** PlatformIO (Arduino Framework).
- **Backend (Python 3.12+):** `websockets`, `numpy`, `matplotlib`
- **Frontend (Web):** *Vanilla JS*, Plotly.js (via CDN).

---
<p align="center"><i>Dibuat untuk kebutuhan Skripsi/Tugas Akhir.</i></p>

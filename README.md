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



## 💻 Dependencies

- **Hardware:** ESP32, Sensor IMU (BNO055/MPU6050), 8x Sensor Jarak (VL53L0X / Ultrasonic).
- **Firmware:** PlatformIO (Arduino Framework).
- **Backend (Python 3.12+):** `websockets`, `numpy`, `matplotlib`
- **Frontend (Web):** *Vanilla JS*, Plotly.js (via CDN).

---
<p align="center"><i>Dibuat untuk kebutuhan Skripsi/Tugas Akhir.</i></p>

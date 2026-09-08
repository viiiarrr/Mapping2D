# 🗺️ Web Visualisasi 2D Sensor Mapper

Visualisasi interaktif hasil pemetaan 2D berbasis sensor IMU Yaw + 8 sensor jarak.

## 🌐 Akses Web

**Link GitHub Pages:**
```
https://<username>.github.io/TugasAkhir/web-visualisasi/
```
*(Ganti `<username>` dengan username GitHub Anda)*

---

## ✨ Fitur

| Fitur | Keterangan |
|-------|-----------|
| 📂 Pilih Percobaan | Dropdown 42 percobaan dari sidebar |
| 📁 Drag & Drop CSV | Upload file `koordinat.csv` langsung ke browser |
| 🔵 Titik Inlier | Titik yang dekat dengan dinding (biru) |
| 🟠 Phantom Point | Titik anomali jauh dari dinding (oranye) |
| 🔴 Nominal Wall | Garis dinding hasil RANSAC fitting (merah) |
| ▶️ Replay Mode | Putar ulang data frame-by-frame dengan slider |
| ⚙️ Parameter Tuning | Ubah EMA alpha, RANSAC threshold, dll secara real-time |
| 📸 Export PNG | Simpan gambar peta |

---

## 🚀 Setup GitHub Pages

### 1. Update data setelah percobaan baru:
```bash
python generate_web_data.py
```

### 2. Push ke GitHub:
```bash
git add web-visualisasi/data/ .github/
git commit -m "Add web visualisasi + data percobaan"
git push
```

### 3. Aktifkan GitHub Pages:
- Buka repo di GitHub
- **Settings → Pages → Source → GitHub Actions**
- GitHub Actions akan otomatis deploy setiap kali push

### 4. Setelah deploy berhasil (±1-2 menit):
- Akses: `https://<username>.github.io/TugasAkhir/web-visualisasi/`

---

## 🗂️ Struktur Folder

```
web-visualisasi/
├── index.html          ← Halaman utama
├── css/
│   └── style.css       ← Dark mode premium styling
├── js/
│   ├── processor.js    ← Algoritma (EMA, RANSAC, Split-Merge, Phantom)
│   └── app.js          ← UI logic + Plotly rendering
└── data/
    ├── manifest.json   ← Daftar semua percobaan (auto-generated)
    ├── percobaan_1/
    │   └── koordinat.csv
    ├── ...
    └── percobaan_42/
        └── koordinat.csv
```

---

## 🧮 Algoritma

Port penuh dari `visualisasi_2d.py` ke JavaScript:
- **EMA Filter** — Rata-rata berbobot per sudut (alpha = 0.25)
- **Outlier Filter** — Median + sigma per sudut (window = 10)
- **Split-and-Merge** — Segmentasi titik cloud menjadi segmen dinding
- **RANSAC Line Fitting** — Fit garis terbaik per segmen
- **Phantom Detection** — Titik yang jauh dari semua wall line

---

## 🖥️ Buka Lokal (tanpa GitHub Pages)

Jalankan server lokal dari root folder TugasAkhir:
```bash
python -m http.server 8000
```
Lalu buka: `http://localhost:8000/web-visualisasi/`

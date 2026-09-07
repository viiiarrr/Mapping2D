"""
Visualisasi 2D Real-Time — Menggunakan sudut IMU (Yaw) dari ESP32

Koreksi logika sudut:
  - CW = yaw NEGATIF  → physical_angle = (-yaw) % 360
  - CCW = yaw POSITIF → physical_angle = (-yaw) % 360  (SAMA!)
  - Formula ini berlaku untuk kedua arah tanpa perlu reset yaw

Stabilitas peta:
  - Peta disimpan per derajat (0-359) dengan EMA
  - Scatter & boundary digambar DARI stable_map (bukan raw points)
  - Obstacle tidak bergerak karena tiap derajat dirata-rata
"""

import socket, threading, numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os, csv, datetime

# =====================
# KONFIGURASI
# =====================
UDP_IP        = "0.0.0.0"
UDP_PORT      = 5005
NUM_SENSOR    = 8
SENSOR_STEP   = 45.0    # Jarak antar sensor (derajat)
EMA_ALPHA     = 0.25    # Bobot data baru (lebih kecil = lebih stabil)
MAX_DIST      = 250.0   # Filter jarak maksimum (cm)
MIN_DIST      = 2.0     # Filter jarak minimum (cm)

# Filter outlier per sudut
# Jika nilai baru menyimpang lebih dari OUTLIER_SIGMA x std_dev dari median
# histori sudut itu, data tersebut DIBUANG (tidak dimasukkan ke EMA)
OUTLIER_SIGMA  = 2.0    # Toleransi deviasi standar
OUTLIER_WINDOW = 10     # Jumlah sampel histori per sudut untuk filter

MIN_COUNT = 4           # Sudut harus diukur minimal N kali agar ditampilkan

class Visualisasi2D:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))

        # Peta stabil: indeks 0-359° → jarak EMA
        # 0 berarti belum ada data
        self.stable_map = np.zeros(360)
        self.count_map  = np.zeros(360, dtype=int)  # Berapa kali sudut ini diisi

        # Histori per sudut untuk filter outlier (ring buffer)
        self.hist_map = [[] for _ in range(360)]

        self.current_yaw = 0.0
        self.record_log  = []
        self.running     = True
        self.paket_count = 0

        # =====================
        # Setup Figure
        # =====================
        self.fig, self.ax = plt.subplots(figsize=(9, 9), facecolor='white')
        self.ax.set_facecolor('white')

        # Scatter titik dari stable_map (biru gelap)
        self.scatter, = self.ax.plot([], [], 'o',
            color='#1a6fb5', markersize=5, alpha=0.85,
            label='Titik Peta (EMA Stabil)', zorder=4)

        # Titik mentah (kecil, transparan) – referensi sensor
        self.boundary, = self.ax.plot([], [], 'o',
            color='#aaaaaa', markersize=2, alpha=0.4,
            label='Titik Sensor (Raw)', zorder=2)

        # Persegi panjang hasil fitting PCA (batas ruangan sesungguhnya)
        self.rect_line, = self.ax.plot([], [], '-',
            color='#cc2222', linewidth=2.2, alpha=0.9,
            label='Batas Ruangan (Fit)', zorder=5)

        # Indikator arah scanner
        self.dir_line, = self.ax.plot([], [], '-',
            color='#e03030', linewidth=2.5, alpha=0.9,
            label='Arah Scanner', zorder=6)
        self.ax.plot(0, 0, 'k+', ms=12, mew=2.5, zorder=7)

        # Batas tampilan & dekorasi
        R = MAX_DIST
        self.ax.set_xlim(-R, R)
        self.ax.set_ylim(-R, R)
        self.ax.set_aspect('equal')
        self.ax.grid(True, ls='--', alpha=0.3, color='#aaaaaa')
        self.ax.axhline(0, color='#888888', lw=0.7, alpha=0.5)
        self.ax.axvline(0, color='#888888', lw=0.7, alpha=0.5)
        self.ax.set_xlabel('X (cm)', color='#333333')
        self.ax.set_ylabel('Y (cm)', color='#333333')
        self.ax.tick_params(colors='#333333')
        for s in self.ax.spines.values():
            s.set_edgecolor('#cccccc')

        self.title_obj = self.ax.set_title(
            'Pemetaan 2D — Menunggu data ESP32...',
            color='#111111', fontsize=13, fontweight='bold', pad=12)
        self.ax.legend(loc='upper right', facecolor='white',
                       labelcolor='#111111', fontsize=8, framealpha=0.9,
                       edgecolor='#cccccc')

        # Lingkaran referensi jarak
        for r in [50, 100, 150, 200]:
            c = plt.Circle((0,0), r, fill=False, color='#aaaaaa',
                           lw=0.6, alpha=0.5)
            self.ax.add_patch(c)
            self.ax.text(r+2, 3, f'{r}cm', color='#888888',
                        fontsize=7, alpha=0.8)

        # Garis arah mata angin (tipis)
        for ang in [0, 45, 90, 135, 180, 225, 270, 315]:
            r = np.radians(ang)
            self.ax.plot([0, R*np.cos(r)], [0, R*np.sin(r)],
                        color='#cccccc', lw=0.4, alpha=0.6)

        # Mulai thread penerima
        self.thread = threading.Thread(target=self._receive, daemon=True)
        self.thread.start()

    # ==========================================
    def _receive(self):
        print(f"[*] UDP listener aktif di port {UDP_PORT}...")
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                self._parse(data.decode('utf-8').strip())
            except Exception as e:
                if self.running:
                    print(f"[!] {e}")

    def _parse(self, message):
        try:
            parts = message.split(',')
            if len(parts) != 9:
                return

            yaw_raw   = float(parts[0])
            distances = [float(x) for x in parts[1:]]
            self.current_yaw = yaw_raw
            self.paket_count += 1

            # Log
            now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.record_log.append(
                [now, round(yaw_raw, 2)] + [round(d, 1) for d in distances])

            for i in range(NUM_SENSOR):
                dist = distances[i]
                if dist < MIN_DIST or dist > MAX_DIST:
                    continue

                # ─────────────────────────────────────────
                # RUMUS KUNCI:
                # CW  = yaw negatif → physical = -yaw → naik positif
                # CCW = yaw positif → physical = -yaw → turun ke 0
                # Keduanya pakai formula SAMA: (-yaw + offset_sensor) % 360
                # ─────────────────────────────────────────
                physical_deg = (-yaw_raw + i * SENSOR_STEP) % 360
                idx = int(physical_deg) % 360

                # ─────────────────────────────────────────
                # FILTER OUTLIER per sudut:
                # Jika histori sudah cukup, tolak data yang menyimpang
                # lebih dari OUTLIER_SIGMA * std dari median histori
                # ─────────────────────────────────────────
                hist = self.hist_map[idx]
                if len(hist) >= OUTLIER_WINDOW:
                    med = np.median(hist)
                    std = np.std(hist)
                    if std > 0 and abs(dist - med) > OUTLIER_SIGMA * std:
                        continue  # Buang data noise/spike

                # Simpan ke histori (ring buffer)
                hist.append(dist)
                if len(hist) > OUTLIER_WINDOW:
                    hist.pop(0)

                # Update EMA di stable_map
                if self.stable_map[idx] == 0:
                    self.stable_map[idx] = dist
                else:
                    self.stable_map[idx] = (
                        (1 - EMA_ALPHA) * self.stable_map[idx]
                        + EMA_ALPHA * dist)
                self.count_map[idx] += 1

        except (ValueError, IndexError):
            pass

    def _fit_rectangle(self, xs, ys):
        """
        Fit persegi panjang ke titik-titik point cloud menggunakan PCA.
        PCA menemukan orientasi utama ruangan secara otomatis,
        lalu bounding rectangle digambar pada sumbu principal tersebut.
        """
        pts = np.column_stack([xs, ys])
        if len(pts) < 10:
            return [], []

        # Pusat massa titik-titik
        center = pts.mean(axis=0)
        pts_c  = pts - center

        # PCA: eigen-decomposition dari covariance matrix
        cov = np.cov(pts_c.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # Urutkan: eigenvalue terbesar = sumbu utama (panjang ruangan)
        order = eigenvalues.argsort()[::-1]
        V = eigenvectors[:, order]          # Kolom = sumbu utama PCA

        # Proyeksikan semua titik ke sumbu PCA
        proj = pts_c @ V

        # Batas rectangle dalam ruang PCA
        lo = proj.min(axis=0)
        hi = proj.max(axis=0)

        # 4 sudut rectangle dalam ruang PCA (polygon tertutup)
        corners_p = np.array([
            [lo[0], lo[1]],
            [hi[0], lo[1]],
            [hi[0], hi[1]],
            [lo[0], hi[1]],
            [lo[0], lo[1]],   # Tutup polygon
        ])

        # Transformasi balik ke koordinat dunia (cm)
        corners = corners_p @ V.T + center
        return corners[:, 0].tolist(), corners[:, 1].tolist()

    def _build_from_map(self):
        """Bangun scatter (titik terfilter) dan rectangle fitting dari stable_map"""
        sx, sy   = [], []   # Titik scatter yang sudah difilter (count >= MIN_COUNT)
        raw_x, raw_y = [], []  # Semua titik mentah (untuk referensi)

        for i in range(360):
            d = self.stable_map[i]
            if d > 0:
                rad = np.radians(i)
                x = d * np.cos(rad)
                y = d * np.sin(rad)
                raw_x.append(x)
                raw_y.append(y)
                # Hanya masukkan ke scatter utama jika cukup terukur
                if self.count_map[i] >= MIN_COUNT:
                    sx.append(x)
                    sy.append(y)

        # Fit rectangle ke titik yang sudah terfilter
        rx, ry = self._fit_rectangle(sx, sy) if len(sx) >= 12 else ([], [])

        return sx, sy, raw_x, raw_y, rx, ry

    def _update_plot(self, frame):
        filled   = int(np.count_nonzero(self.stable_map))
        filtered = int(np.sum(self.count_map >= MIN_COUNT))

        # Indikator arah scanner
        a = np.radians((-self.current_yaw) % 360)
        self.dir_line.set_data(
            [0, 15 * np.cos(a)],
            [0, 15 * np.sin(a)])

        # Update title
        self.title_obj.set_text(
            f'Pemetaan 2D (IMU Yaw)  |  '
            f'{filtered}/{filled} sudut stabil  |  '
            f'Yaw: {self.current_yaw:.1f}°  |  '
            f'Paket: {self.paket_count}')

        if filled == 0:
            return self.scatter, self.boundary, self.rect_line, self.dir_line, self.title_obj

        # Bangun dari stable_map
        sx, sy, raw_x, raw_y, rx, ry = self._build_from_map()
        self.scatter.set_data(sx, sy)          # Titik biru terfilter
        self.boundary.set_data(raw_x, raw_y)   # Titik abu mentah
        self.rect_line.set_data(rx, ry)        # Rectangle PCA fitting

        return self.scatter, self.boundary, self.rect_line, self.dir_line, self.title_obj

    def save_data(self):
        if not self.record_log:
            print("\n[-] Tidak ada data. Simpan dilewati.")
            return
        base = "Data"
        os.makedirs(base, exist_ok=True)
        idx = 1
        while os.path.exists(os.path.join(base, f"percobaan_{idx}")):
            idx += 1
        d = os.path.join(base, f"percobaan_{idx}")
        os.makedirs(d)
        with open(os.path.join(d, "koordinat.csv"), 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(["Waktu", "Yaw_IMU"] +
                        [f"Sensor_{i+1}" for i in range(8)])
            w.writerows(self.record_log)
        self.fig.savefig(os.path.join(d, "peta_2d.png"),
                         dpi=300, bbox_inches='tight',
                         facecolor='white')
        print(f"\n[+] Tersimpan: {d}")
        print(f"    {len(self.record_log)} baris | "
              f"{int(np.count_nonzero(self.stable_map))}/360 sudut terpetakan")

    def start(self):
        self.anim = FuncAnimation(
            self.fig, self._update_plot,
            interval=150, blit=True, cache_frame_data=False)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    app = Visualisasi2D()
    try:
        app.start()
    except KeyboardInterrupt:
        print("\n[!] Menutup...")
    finally:
        app.running = False
        app.save_data()
        app.sock.close()

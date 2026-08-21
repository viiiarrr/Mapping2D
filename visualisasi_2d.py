import socket
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import savgol_filter
from matplotlib.patches import Polygon
import os
import csv
import datetime
class LidarScanner2D:
    def __init__(self, ip="0.0.0.0", port=5005):
        # Konfigurasi Jaringan
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        
        # Buffer Data: Menggunakan dictionary untuk menyimpan jarak terbaru di setiap sudut derajat (0-359)
        self.map_data = {}
        self.current_angle_deg = 0.0
        self.latest_rays_x = []
        self.latest_rays_y = []
        
        # Buffer untuk rekaman data log (CSV)
        self.record_log = []
        
        # State Thread
        self.running = True
        
        # Setup Figure Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        
        # Elemen plot untuk titik mentah (NWA filtered) dan garis mulus (Savitzky-Golay)
        self.scatter_raw, = self.ax.plot([], [], 'ro', markersize=4, alpha=0.5, label="Raw / NWA Valid Data")
        self.line_smooth, = self.ax.plot([], [], 'b-', linewidth=2, label="Smoothed Boundary (SavGol)")
        
        # Elemen plot untuk sinar laser (biru muda) dan penunjuk arah (merah)
        self.rays_lines, = self.ax.plot([], [], 'c-', linewidth=1, alpha=0.5, label="Sinar Sensor Aktual")
        self.scanner_poly = Polygon([[0,0], [0,0], [0,0]], closed=True, facecolor='red', edgecolor='darkred', alpha=0.8, zorder=10)
        self.ax.add_patch(self.scanner_poly)
        
        # Pengaturan Tampilan Plot
        self.ax.set_xlim(-400, 400) # Asumsi maksimal jangkauan HC-SR04 adalah 400cm
        self.ax.set_ylim(-400, 400)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.axhline(0, color='black', linewidth=0.5)
        self.ax.axvline(0, color='black', linewidth=0.5)
        self.ax.set_title("Stasiun Penerima: Pemetaan 2D Statis", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Sumbu X (cm)")
        self.ax.set_ylabel("Sumbu Y (cm)")
        self.ax.legend(loc="upper right")
        
        # Memulai thread penerima data agar tidak memblokir antarmuka GUI (Plot)
        self.thread = threading.Thread(target=self.receive_data, daemon=True)
        self.thread.start()

    def receive_data(self):
        """Tahap 1: Penerimaan Data (Networking)"""
        print(f"[*] Mendengarkan data UDP di {self.ip}:{self.port}...")
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8').strip()
                self.parse_and_store_data(message)
            except Exception as e:
                print(f"[!] Error saat menerima data: {e}")

    def parse_and_store_data(self, message):
        """Tahap 2a: Parsing Data dan Kalkulasi Sudut Absolut"""
        try:
            # Format pesan dari ESP32: servo_angle, dist_1, dist_2, ..., dist_8
            values = list(map(float, message.split(',')))
            if len(values) < 9:
                return
                
            servo_angle = values[0]
            self.current_angle_deg = servo_angle
            distances = values[1:9]
            
            curr_rays_x = []
            curr_rays_y = []
            
            # Waktu terima paket
            now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            for i in range(8):
                dist = distances[i]
                
                # Menghitung sudut aktual (sensor ke-i dipasang berjarak 45 derajat)
                actual_angle_deg = (servo_angle + (i * 45)) % 360
                
                # Simpan titik sinar untuk digambar (jika valid)
                if dist > 0 and dist <= 400:
                    rad = np.radians(actual_angle_deg)
                    x = dist * np.cos(rad)
                    y = dist * np.sin(rad)
                    curr_rays_x.extend([0, x, None])
                    curr_rays_y.extend([0, y, None])
                    
                    # Tambahkan data ini ke dalam log rekaman
                    self.record_log.append([now_str, round(actual_angle_deg, 1), dist, round(x, 2), round(y, 2)])
                
                # Mengabaikan pembacaan error (misal 0 atau di luar jangkauan sensor > 400cm)
                if dist <= 0 or dist > 400:
                    continue
                    
                # Menyimpan jarak pada sudut yang dibulatkan ke integer (0-359 derajat)
                # Ini otomatis memperbarui (overwrite) pemetaan saat piringan menyapu area yang sama
                idx = int(round(actual_angle_deg)) % 360
                self.map_data[idx] = dist
                
            self.latest_rays_x = curr_rays_x
            self.latest_rays_y = curr_rays_y
                
        except ValueError:
            pass

    def filter_nwa(self, x_arr, y_arr, threshold=30.0):
        """Tahap 2c: Filter Nominal Wall Angle (NWA) / Menghapus Phantom Points"""
        if len(x_arr) < 2:
            return x_arr, y_arr
            
        valid_x = [x_arr[0]]
        valid_y = [y_arr[0]]
        
        for i in range(1, len(x_arr)):
            # Menghitung jarak euclidian antara titik saat ini dengan titik sebelumnya
            jarak_antar_titik = np.hypot(x_arr[i] - valid_x[-1], y_arr[i] - valid_y[-1])
            
            # Jika selisihnya lebih kecil dari threshold, titik tersebut dianggap valid
            # Jika melebihi threshold, titik tersebut dianggap phantom point dan diabaikan (drop)
            if jarak_antar_titik <= threshold:
                valid_x.append(x_arr[i])
                valid_y.append(y_arr[i])
                
        return np.array(valid_x), np.array(valid_y)

    def apply_savgol_filter(self, x_arr, y_arr, window=11, poly=3):
        """Tahap 2d: Filter Savitzky-Golay untuk menghaluskan kontur garis ruangan"""
        # Syarat filter: panjang data harus lebih besar dari window_length, dan window_length ganjil
        if len(x_arr) < window:
            return x_arr, y_arr
            
        x_smooth = savgol_filter(x_arr, window_length=window, polyorder=poly)
        y_smooth = savgol_filter(y_arr, window_length=window, polyorder=poly)
        return x_smooth, y_smooth

    def update_plot(self, frame):
        """Tahap 3: Pemrosesan Plotting Visualisasi 2D Real-Time"""
        
        # 1. Update arah kepala scanner (Segitiga Merah)
        angle_rad = np.radians(self.current_angle_deg)
        tip_x = 30 * np.cos(angle_rad)
        tip_y = 30 * np.sin(angle_rad)
        left_x = 10 * np.cos(angle_rad + np.pi/2)
        left_y = 10 * np.sin(angle_rad + np.pi/2)
        right_x = 10 * np.cos(angle_rad - np.pi/2)
        right_y = 10 * np.sin(angle_rad - np.pi/2)
        self.scanner_poly.set_xy([[left_x, left_y], [tip_x, tip_y], [right_x, right_y]])
        
        # 2. Update Sinar Sensor (Garis Biru)
        self.rays_lines.set_data(self.latest_rays_x, self.latest_rays_y)
        
        if not self.map_data:
            return self.scatter_raw, self.line_smooth, self.rays_lines, self.scanner_poly
            
        # Mengekstrak sudut yang sudah terurut dari 0-359 derajat dari buffer dictionary
        angles_deg = sorted(self.map_data.keys())
        distances = [self.map_data[a] for a in angles_deg]
        
        angles_rad_map = np.radians(angles_deg)
        dists = np.array(distances)
        
        # Tahap 2b: Homogeneous Transformation Matrix (Konversi Polar ke Kartesius 2D)
        x_raw = dists * np.cos(angles_rad_map)
        y_raw = dists * np.sin(angles_rad_map)
        
        # Menerapkan Filter NWA untuk membersihkan outlier
        # Threshold dinaikkan menjadi 250 agar sudut tajam segitiga tidak dianggap sebagai error dan dibuang
        x_nwa, y_nwa = self.filter_nwa(x_raw, y_raw, threshold=250.0)
        
        # Memperbarui data untuk scatter plot (titik merah)
        self.scatter_raw.set_data(x_nwa, y_nwa)
        
        # Menerapkan Filter Savitzky-Golay untuk membuat garis dinding yang halus
        if len(x_nwa) >= 11: 
            x_smooth, y_smooth = self.apply_savgol_filter(x_nwa, y_nwa, window=11, poly=3)
            self.line_smooth.set_data(x_smooth, y_smooth)
        else:
            self.line_smooth.set_data([], [])
            
        return self.scatter_raw, self.line_smooth, self.rays_lines, self.scanner_poly

    def save_data(self):
        """Menyimpan log koordinat dan gambar grafik ke dalam folder percobaan"""
        if not self.record_log:
            print("\n[-] Tidak ada data valid yang diterima. Proses simpan dilewati.")
            return
            
        base_dir = "Data"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            
        # Mencari nomor percobaan terakhir
        idx = 1
        while os.path.exists(os.path.join(base_dir, f"percobaan_{idx}")):
            idx += 1
            
        save_dir = os.path.join(base_dir, f"percobaan_{idx}")
        os.makedirs(save_dir)
        
        # 1. Simpan File Excel/CSV
        csv_path = os.path.join(save_dir, "koordinat.csv")
        try:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Waktu", "Sudut_Derajat", "Jarak_cm", "Koordinat_X", "Koordinat_Y"])
                writer.writerows(self.record_log)
        except Exception as e:
            print(f"[!] Gagal menyimpan CSV: {e}")
            
        # 2. Simpan Gambar Peta 2D
        fig_path = os.path.join(save_dir, "peta_2d.png")
        try:
            # Karena plt.show() sudah ditutup, kita simpan figure yang ada di memory
            self.fig.savefig(fig_path, dpi=300, bbox_inches='tight')
            print(f"\n[+] Data berhasil disimpan!")
            print(f"    - Folder : {save_dir}")
            print(f"    - Data   : {len(self.record_log)} baris rekaman tersimpan (koordinat.csv)")
            print(f"    - Gambar : peta_2d.png")
        except Exception as e:
            print(f"[!] Gagal menyimpan gambar: {e}")

    def start(self):
        """Memulai animasi matplotlib secara terus-menerus (looping)"""
        # FuncAnimation memanggil self.update_plot setiap 100 milidetik
        self.anim = FuncAnimation(self.fig, self.update_plot, interval=100, blit=True, cache_frame_data=False)
        plt.show()

if __name__ == "__main__":
    # Inisialisasi Program. 0.0.0.0 artinya listen ke semua interface.
    app = LidarScanner2D(ip="0.0.0.0", port=5005)
    
    try:
        app.start()
    except KeyboardInterrupt:
        print("\n[!] Menutup program...")
    finally:
        app.running = False
        app.save_data()
        app.sock.close()

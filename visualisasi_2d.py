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
        
        # Buffer Data:
        # map_data: 1 nilai per sudut (untuk batas ruangan)
        # all_points_x/y: semua titik mentah (untuk point cloud)
        self.map_data   = {}
        self.all_points_x = []
        self.all_points_y = []
        self.current_angle_deg = 0.0
        self.latest_rays_x = []
        self.latest_rays_y = []
        
        # Buffer untuk rekaman data log (CSV)
        self.record_log = []
        
        # State Thread
        self.running = True
        
        # Flag: Pemetaan selesai (map dikunci, tidak diupdate lagi)
        # Ruangan tidak bergerak, jadi 1x scan sudah cukup!
        self.mapping_complete = False
        self.mapping_locked_at = 0  # Berapa sudut unik sudah terpetakan
        
        # Setup Figure Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        
        # Elemen plot untuk titik mentah (NWA filtered) dan garis mulus (Savitzky-Golay)
        self.scatter_raw, = self.ax.plot([], [], 'ro', markersize=4, alpha=0.5, label="Raw / NWA Valid Data")
        self.line_smooth, = self.ax.plot([], [], 'b-', linewidth=2, label="Smoothed Boundary (SavGol)")
        
        # Elemen plot untuk sinar laser (biru muda) dan penunjuk arah (merah)
        self.rays_lines, = self.ax.plot([], [], 'c-', linewidth=1, alpha=0.5, label="Sinar Sensor Aktual")
        self.scanner_poly = Polygon([[0,0], [0,0], [0,0]], closed=True, facecolor='red', edgecolor='darkred', alpha=0.8, zorder=10)
        self.ax.add_patch(self.scanner_poly)
        
        # Pengaturan Tampilan Plot (Batas Zoom diset 1 meter / 100 cm)
        self.ax.set_xlim(-100, 100) 
        self.ax.set_ylim(-100, 100)
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
        """Parsing data: sudut platform + offset sensor = arah absolut setiap sensor"""
        try:
            parts = message.split(',')
            if len(parts) == 9:
                servo_angle = float(parts[0])  # Sudut platform saat ini (dari step servo)
                self.current_angle_deg = servo_angle
                distances = [float(x) for x in parts[1:]]
                
                # Waktu terima paket
                import datetime, time
                now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                log_row = [now_str, round(servo_angle, 1)] + [round(d, 1) for d in distances]
                self.record_log.append(log_row)
                
                curr_rays_x = [0]
                curr_rays_y = [0]
                
                for i in range(8):
                    dist = distances[i]
                    # Sudut absolut = sudut platform + offset posisi sensor di piringan
                    # Sensor 0 = platform angle, Sensor 1 = platform angle + 45°, dst.
                    actual_angle_deg = (servo_angle + (i * 45)) % 360
                    angle_rad = np.radians(actual_angle_deg)
                    
                    # Update garis sinar
                    if dist > 0 and dist <= 400:
                        curr_rays_x.extend([dist * np.cos(angle_rad), 0])
                        curr_rays_y.extend([dist * np.sin(angle_rad), 0])
                    
                    # Simpan ke peta dengan EMA filter untuk mengurangi noise
                    # HANYA update jika pemetaan belum selesai!
                    if not self.mapping_complete:
                        if dist > 0 and dist <= 400:
                            idx = int(round(actual_angle_deg)) % 360
                            if idx in self.map_data:
                                old_dist, _ = self.map_data[idx]
                                dist_ema = 0.7 * old_dist + 0.3 * dist
                            else:
                                dist_ema = dist
                            self.map_data[idx] = (dist_ema, time.time())
                            
                            # Simpan juga ke all_points untuk point cloud yang dense
                            x_pt = dist * np.cos(angle_rad)
                            y_pt = dist * np.sin(angle_rad)
                            self.all_points_x.append(x_pt)
                            self.all_points_y.append(y_pt)
                            # Batasi maksimal 5000 titik agar tidak berat
                            if len(self.all_points_x) > 5000:
                                self.all_points_x = self.all_points_x[-5000:]
                                self.all_points_y = self.all_points_y[-5000:]
                    
                        # Cek apakah 1 putaran penuh sudah selesai (min 300 sudut unik terpetakan)
                        if len(self.map_data) >= 300 and not self.mapping_complete:
                            self.mapping_complete = True
                            self.mapping_locked_at = len(self.map_data)
                            print(f"\n[✓] PEMETAAN SELESAI! {self.mapping_locked_at} sudut terpetakan.")
                            print(f"    Map DIKUNCI - ruangan tidak akan bergerak lagi!")
                
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

    def spatial_clustering(self, x_arr, y_arr, threshold=30.0):
        """Metode Spatial Clustering yang disempurnakan (Anchor/Kunci) agar titik DIAM SEMPURNA (Tanpa Jitter)"""
        if len(x_arr) == 0:
            return [], []
            
        clustered_x = []
        clustered_y = []
        
        for x, y in zip(x_arr, y_arr):
            found_cluster = False
            for cx, cy in zip(clustered_x, clustered_y):
                # Jika titik ini berdekatan dengan cluster yang sudah ada
                if np.hypot(x - cx, y - cy) < threshold:
                    found_cluster = True
                    # Titik ini "disedot" ke cluster yang sudah ada, JANGAN ubah pusat clusternya
                    break
                    
            if not found_cluster:
                # Bikin cluster baru dan KUNCI posisinya di titik ini
                # Karena posisinya dikunci (tidak di rata-rata), titik di layar tidak akan bergetar/bergerak sama sekali
                clustered_x.append(x)
                clustered_y.append(y)
                
        return clustered_x, clustered_y

    def update_plot(self, frame):
        """Tahap 3: Pemrosesan Plotting Visualisasi 2D Real-Time"""
        
        # 1. Update arah kepala scanner (Segitiga Merah)
        angle_rad = np.radians(self.current_angle_deg)
        tip_x = 10 * np.cos(angle_rad)
        tip_y = 10 * np.sin(angle_rad)
        left_x = 3 * np.cos(angle_rad + np.pi/2)
        left_y = 3 * np.sin(angle_rad + np.pi/2)
        right_x = 3 * np.cos(angle_rad - np.pi/2)
        right_y = 3 * np.sin(angle_rad - np.pi/2)
        self.scanner_poly.set_xy([[left_x, left_y], [tip_x, tip_y], [right_x, right_y]])
        
        # 2. Update Sinar Sensor (Garis Biru)
        self.rays_lines.set_data(self.latest_rays_x, self.latest_rays_y)
        
        if not self.map_data:
            return self.scatter_raw, self.line_smooth, self.rays_lines, self.scanner_poly
            
        import time
        current_time = time.time()
        
        n_angles = len(self.map_data)
        
        # =====================================================
        # FASE 1: Tunjukkan titik-titik yang sedang terkumpul
        # =====================================================
        if n_angles < 200:
            # Tampilkan semua titik mentah yang sudah terkumpul
            self.scatter_raw.set_data(self.all_points_x, self.all_points_y)
            self.line_smooth.set_data([], [])
            self.ax.set_title(f"Mengumpulkan data... ({n_angles}/360 sudut)", fontsize=13)
            return self.scatter_raw, self.line_smooth, self.rays_lines, self.scanner_poly
        
        # =====================================================
        # FASE 2: Data cukup → Tampilkan titik + batas ruangan
        # =====================================================
        self.ax.set_title("Peta 2D Ruangan (SELESAI)", fontsize=14, fontweight='bold', color='green')
        
        # Tampilkan semua titik mentah (point cloud dense)
        self.scatter_raw.set_data(self.all_points_x, self.all_points_y)
        
        # Buat garis batas ruangan dari data map (1 nilai per sudut, sudah EMA)
        sorted_angles = sorted(self.map_data.keys())
        sorted_dists  = [self.map_data[a][0] for a in sorted_angles]
        
        angles_rad = np.radians(sorted_angles)
        dists_arr  = np.array(sorted_dists)
        
        # Koordinat kartesius titik batas dinding
        wall_x = dists_arr * np.cos(angles_rad)
        wall_y = dists_arr * np.sin(angles_rad)
        
        # Tutup poligon dan gambar batas ruangan (merah tebal, seperti referensi)
        closed_x = np.append(wall_x, wall_x[0])
        closed_y = np.append(wall_y, wall_y[0])
        self.line_smooth.set_data(closed_x, closed_y)
        self.line_smooth.set_color('red')
        self.line_smooth.set_linewidth(2.5)
        
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
                writer.writerow(["Waktu", "Sudut_Servo", "Sensor_1", "Sensor_2", "Sensor_3", "Sensor_4", "Sensor_5", "Sensor_6", "Sensor_7", "Sensor_8"])
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

"""
UDP Receiver Test - Penerima data dari ESP32 via WiFi
Jalankan program ini di laptop saat ESP32 berjalan dengan baterai.

Prasyarat:
- Laptop dan ESP32 terhubung ke WiFi yang sama ("rytz")
- IP laptop harus 192.168.137.1 (Mobile Hotspot Windows)
  Atau sesuaikan dengan IP laptop Anda

Cara cek IP laptop (Windows):
  ipconfig -> lihat bagian "WiFi" atau "Mobile Hotspot"
"""

import socket
import datetime

# ==========================================
# KONFIGURASI
# ==========================================
LISTEN_IP   = "0.0.0.0"   # Dengarkan dari semua interface
LISTEN_PORT = 5005         # Harus sama dengan udp_port di ESP32

# ==========================================
# INISIALISASI SOCKET
# ==========================================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.settimeout(10)  # Timeout 10 detik jika tidak ada data

print("=" * 60)
print("  UDP RECEIVER — Menunggu data dari ESP32...")
print(f"  Dengarkan di: {LISTEN_IP}:{LISTEN_PORT}")
print("  Tekan Ctrl+C untuk berhenti")
print("=" * 60)

paket_diterima = 0

try:
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8').strip()
            paket_diterima += 1
            waktu = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Parse data: sudut,s1,s2,s3,s4,s5,s6,s7,s8
            parts = message.split(',')
            if len(parts) == 9:
                yaw   = float(parts[0])
                jarak = [float(x) for x in parts[1:]]

                print(f"[{waktu}] #{paket_diterima:04d} | IP: {addr[0]}")
                print(f"  YAW   : {yaw:.1f}°")
                print(f"  Sensor: {' | '.join([f'S{i+1}={jarak[i]:.1f}cm' for i in range(8)])}")
                print()
            else:
                # Tampilkan raw jika format tidak sesuai
                print(f"[{waktu}] RAW ({len(parts)} bagian): {message}")

        except socket.timeout:
            print(f"[!] Tidak ada data selama 10 detik... (paket diterima: {paket_diterima})")
            print("    Pastikan ESP32 menyala, terhubung WiFi, dan IP laptop benar.")

except KeyboardInterrupt:
    print(f"\n[*] Dihentikan. Total paket diterima: {paket_diterima}")
finally:
    sock.close()

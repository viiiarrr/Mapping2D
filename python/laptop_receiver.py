import socket
import json

# ==========================================
# KONFIGURASI UDP (Penerima di Laptop)
# ==========================================
# Dengarkan di semua IP (0.0.0.0) di port 5005
UDP_IP = "0.0.0.0"
UDP_PORT = 5005

def main():
    # Inisialisasi Socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"Menunggu data dari Raspberry Pi di port {UDP_PORT}...")
    
    try:
        while True:
            # Terima paket data (buffer size 1024 bytes)
            data, addr = sock.recvfrom(1024)
            pesan = data.decode('utf-8')
            
            try:
                # Parse data JSON dari string
                sensor_data = json.loads(pesan)
                
                # Ekstrak data untuk diproses
                angle = sensor_data.get('angle')
                distances = sensor_data.get('distances')
                
                # Di sini Anda bisa menambahkan logika pengolahan data Anda
                # Misalnya memplot grafik, mendeteksi objek, dsb.
                print(f"[Data Masuk dari {addr[0]}] Sudut: {angle} | Jarak: {distances}")
                
            except json.JSONDecodeError:
                print(f"Menerima data (Bukan JSON): {pesan}")
                
    except KeyboardInterrupt:
        print("\nProgram dihentikan.")
    finally:
        sock.close()

if __name__ == '__main__':
    main()

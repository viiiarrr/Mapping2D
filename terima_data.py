import socket

# Konfigurasi IP dan Port
# Harus sama dengan udp_port yang ada di ESP32
UDP_IP = "0.0.0.0" # Mendengarkan dari semua IP (biarkan 0.0.0.0)
UDP_PORT = 5005    # Port yang diatur di ESP32

# Membuat socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Menunggu data UDP di port {UDP_PORT}...")
print("Tekan Ctrl+C untuk berhenti.")

try:
    while True:
        # Menerima data dengan ukuran buffer 1024 bytes
        data, addr = sock.recvfrom(1024)
        
        # Data yang diterima berupa bytes, kita decode menjadi string
        pesan = data.decode('utf-8')
        
        # Menampilkan data yang diterima dari ESP32
        print(f"Dari {addr[0]}: {pesan}")
        
except KeyboardInterrupt:
    print("\nProgram dihentikan.")
finally:
    sock.close()

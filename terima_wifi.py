import socket

# Konfigurasi Port (Harus sama dengan di ESP32)
UDP_PORT = 5005

# Buat socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Dengarkan dari semua IP masuk (0.0.0.0) di port 5005
sock.bind(("0.0.0.0", UDP_PORT))

print(f"Menunggu data sensor nirkabel dari ESP32 di port {UDP_PORT}...")
print("Pastikan laptop dan ESP32 terhubung ke hotspot HP yang sama.")
print("-" * 50)

try:
    while True:
        # Terima data maksimal 1024 bytes
        data, address = sock.recvfrom(1024)
        
        # Terjemahkan data dari byte ke teks (string)
        pesan = data.decode('utf-8')
        
        # Tampilkan data di terminal
        print(f"📡 Dari ESP32 {address[0]} -> {pesan}")
        
except KeyboardInterrupt:
    print("\nProgram Penerima UDP dihentikan.")

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
        
        # Menampilkan pesan asli (mentah)
        # print(f"Raw data dari {addr[0]}: {pesan}")
        
        # Mengekstrak data dari 8 sensor
        if pesan.startswith("DataSensor:"):
            try:
                # Format: "DataSensor:12.5,-1.0,45.2,..."
                data_str = pesan.replace("DataSensor:", "").strip()
                jarak_list = data_str.split(",")
                
                print("\n=== Data 8 Sensor Ultrasonik ===")
                for i, jarak in enumerate(jarak_list):
                    val = float(jarak)
                    if val == -1.0:
                        print(f"Sensor {i+1}: Tidak Terhubung / Out of Range")
                    else:
                        print(f"Sensor {i+1}: {val} cm")
                print("================================\n")
            except Exception as e:
                print(f"Error parsing data: {e} | Pesan: {pesan}")
        else:
            print(f"[Pesan Lain] {pesan}")
        
except KeyboardInterrupt:
    print("\nProgram dihentikan.")
finally:
    sock.close()

import serial
import socket
import time
import json

# ==========================================
# KONFIGURASI SERIAL (Koneksi ke ESP32)
# ==========================================
# Di Raspberry Pi Linux, port biasanya /dev/ttyUSB0 atau /dev/ttyACM0
# Sesuaikan port ini jika ESP32 dicolokkan dan terbaca berbeda
SERIAL_PORT = '/dev/ttyUSB0'  
BAUD_RATE = 115200

# ==========================================
# KONFIGURASI UDP (Koneksi ke Laptop)
# ==========================================
# Masukkan IP Address Laptop Anda di sini
LAPTOP_IP = '192.168.1.100'  # GANTI DENGAN IP LAPTOP ANDA
UDP_PORT = 5005

# Inisialisasi Socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def main():
    print(f"Mencoba membuka port serial {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("Berhasil terhubung ke ESP32!")
        time.sleep(2) # Tunggu ESP32 reset
        
        while True:
            if ser.in_waiting > 0:
                # Baca baris data dari Serial (ESP32)
                line = ser.readline().decode('utf-8').strip()
                
                if line:
                    # ESP32 mengirim format: angle,d1,d2,d3,d4,d5,d6,d7,d8
                    data_array = line.split(',')
                    
                    if len(data_array) == 9:
                        try:
                            # Parse data menjadi dictionary/JSON agar rapi
                            sensor_data = {
                                "angle": float(data_array[0]),
                                "distances": [float(x) for x in data_array[1:]]
                            }
                            
                            # Ubah dictionary ke bentuk string JSON
                            pesan_json = json.dumps(sensor_data)
                            
                            # Kirim ke Laptop via Wi-Fi (UDP)
                            sock.sendto(pesan_json.encode('utf-8'), (LAPTOP_IP, UDP_PORT))
                            print(f"Terkirim ke Laptop: {pesan_json}")
                            
                        except ValueError:
                            print(f"Data tidak valid (gagal parse angka): {line}")
                    else:
                        print(f"Format data salah (jumlah elemen bukan 9): {line}")
                        
    except serial.SerialException as e:
        print(f"Error membuka port serial: {e}")
        print("Pastikan kabel USB terhubung dan port benar (/dev/ttyUSB0).")
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh user.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
        sock.close()

if __name__ == '__main__':
    main()

#include "Sensor.h"
#include <Arduino.h>
#include <ESP32Servo.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// =====================
// KONFIGURASI WIFI & UDP
// =====================
const char *ssid = "rytz";               // <-- ISI NAMA HOTSPOT HP ANDA
const char *password = "admin12345";     // <-- ISI PASSWORD HOTSPOT HP ANDA
const char *laptop_ip = "192.168.137.1"; // IP Laptop Anda (dari hotspot)
const int udp_port = 5005;

WiFiUDP udp;

// =====================
// KONFIGURASI PIN
// =====================
// Sensor 1 sekarang menggunakan Trig: 18, Echo: 19 sesuai wiring
const int trigPins[NUM_SENSOR] = {19, 5, 4, 23, 22, 25, 27, 12};
const int echoPins[NUM_SENSOR] = {18, 35, 34, 32, 33, 26, 14, 13};

// =====================
// KONFIGURASI SERVO (KODE BARU)
// =====================
Servo myServo;
int servoPin = 21;
// Waktu putar diperbesar drastis karena tegangan modul XL sudah diturunkan (servo lebih lambat).
// Semakin besar angkanya, semakin jauh/lebar putarannya (sudutnya bertambah).
int waktuPutarKanan = 10000; // Coba 6 detik (6000ms), tambah/kurangi jika sudutnya kurang pas
int waktuPutarKiri = 10500;  // Coba 6.5 detik (6500ms) untuk baliknya

// =====================
// INISIALISASI OBJEK
// =====================
Sensor ultrasonicArray(trigPins, echoPins);

// Variabel untuk Non-Blocking Servo & Estimasi Sudut
unsigned long stateStartTime = 0;
int servoState = 0; // 0:Kanan, 1:Berhenti, 2:Kiri, 3:Berhenti
float estimated_angle = 0.0;

void setup() {
  Serial.begin(115200);

  // Inisialisasi Wi-Fi (DIBERI TIMEOUT AGAR TIDAK STUCK)
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED &&
         attempts < 10) { // Maksimal tunggu 5 detik
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi Connected! IP ESP32: " + WiFi.localIP().toString());
  } else {
    Serial.println(
        "\nWi-Fi GAGAL TERSAMBUNG! Melanjutkan program tanpa WiFi...");
  }

  // Inisialisasi sensor
  ultrasonicArray.begin();

  // Inisialisasi Servo (Sesuai kode Anda)
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  myServo.setPeriodHertz(50);
  myServo.attach(servoPin, 500, 2400);

  Serial.println("Memulai Test Servo 360...");
}

void loop() {
  unsigned long currentMillis = millis();
  
  // =========================================
  // 1. LOGIKA SERVO TANPA DELAY (NON-BLOCKING)
  // =========================================
  if (servoState == 0) { // Putar Kanan
    myServo.write(180);
    // Asumsi putaran penuh adalah 180 derajat sweep
    estimated_angle = ((float)(currentMillis - stateStartTime) / waktuPutarKanan) * 180.0;
    if (estimated_angle > 180.0) estimated_angle = 180.0;
    
    if (currentMillis - stateStartTime >= waktuPutarKanan) {
      servoState = 1;
      stateStartTime = currentMillis;
      myServo.write(90); // Berhenti
    }
  } 
  else if (servoState == 1) { // Berhenti Sejenak 1
    if (currentMillis - stateStartTime >= 1000) {
      servoState = 2;
      stateStartTime = currentMillis;
    }
  } 
  else if (servoState == 2) { // Putar Kiri
    myServo.write(0);
    estimated_angle = 180.0 - (((float)(currentMillis - stateStartTime) / waktuPutarKiri) * 180.0);
    if (estimated_angle < 0.0) estimated_angle = 0.0;
    
    if (currentMillis - stateStartTime >= waktuPutarKiri) {
      servoState = 3;
      stateStartTime = currentMillis;
      myServo.write(90); // Berhenti
    }
  } 
  else if (servoState == 3) { // Berhenti Sejenak 2
    if (currentMillis - stateStartTime >= 1000) {
      servoState = 0;
      stateStartTime = currentMillis;
    }
  }

  // =========================================
  // 2. BACA SENSOR LEBIH CEPAT
  // =========================================
  ultrasonicArray.readAll(); 
  
  // Format data WAJIB untuk Python: sudut,jarak1,jarak2,...,jarak8
  String output_str = String(estimated_angle, 1) + ",";
  for (int i = 0; i < NUM_SENSOR; i++) {
    float jarak = ultrasonicArray.getDistance(i);
    // Jika sensor tidak terbaca, kirim 0 agar difilter oleh Python (daripada -1)
    if (jarak == -1.0) jarak = 0.0; 
    
    output_str += String(jarak, 1);
    if (i < NUM_SENSOR - 1) {
      output_str += ","; 
    }
  }
  
  // =========================================
  // 3. KIRIM DATA KE PYTHON
  // =========================================
  if (WiFi.status() == WL_CONNECTED) {
    udp.beginPacket(laptop_ip, udp_port);
    udp.print(output_str);
    udp.endPacket();
  }

  /* --- KODE LAMA DI-COMMENT DULU AGAR FOKUS TEST SENSOR ---
  // 1. BACA SENSOR BERGILIRAN
  ultrasonicArray.readAll();

  // 2. KUMPULKAN DATA KE DALAM STRING (DENGAN SIMULASI DUMMY RUANGAN)
  float current_angle = myServo.getAngle();

  // Jika motor belum dipasang dan tidak berputar, mari kita simulasikan
  sudutnya berputar static float simulated_angle = 0.0; static bool direction =
  true; if (current_angle == 0) { simulated_angle += (direction ? 5.0 : -5.0);
     if (simulated_angle >= 50.0) direction = false;
     if (simulated_angle <= 0.0) direction = true;
     current_angle = simulated_angle;
  }

  String data_sensor = String(current_angle, 1) + ",";
  for (int i = 0; i < NUM_SENSOR; i++) {
    // ---- MODE SIMULASI RUANGAN SEGITIGA ----
    float actual_angle_deg = fmod((current_angle + (i * 45.0)), 360.0);

    // Simulasi dinding ruangan berbentuk segitiga sama sisi dengan jarak 150cm
  ke dinding terdekat float W = 150.0; float dummy_distance = 400.0;

    // Segitiga memiliki 3 dinding. Kita hitung jarak pantulan berdasarkan 3
  arah normal dinding (90, 210, 330 derajat) if (actual_angle_deg >= 30.0 &&
  actual_angle_deg < 150.0) {
        // Dinding Atas
        dummy_distance = W / cos((actual_angle_deg - 90.0) * PI / 180.0);
    } else if (actual_angle_deg >= 150.0 && actual_angle_deg < 270.0) {
        // Dinding Kiri Bawah
        dummy_distance = W / cos((actual_angle_deg - 210.0) * PI / 180.0);
    } else {
        // Dinding Kanan Bawah
        dummy_distance = W / cos((actual_angle_deg - 330.0) * PI / 180.0);
    }

    // Pastikan nilai selalu positif
    dummy_distance = abs(dummy_distance);

    // Tambahkan sedikit noise/acak (±3cm) agar terlihat seperti sensor asli
    dummy_distance += random(-3, 4);
    // ----------------------------------------

    // Masukkan data simulasi ini ke string (menggantikan pembacaan sensor asli)
    data_sensor += String(dummy_distance, 1);

    if (i < NUM_SENSOR - 1) {
      data_sensor += ",";
    }
  }

  // 3. KIRIM DATA KE LAPTOP VIA UDP
  udp.beginPacket(laptop_ip, udp_port);
  udp.print(data_sensor);
  udp.endPacket();

  // (Opsional) Tetap tampilkan di Serial Monitor laptop untuk debugging jika
  dicolok kabel Serial.println(data_sensor);

  // 3. GERAKKAN SERVO (Pengganti Stepper)
  myServo.moveAngle(5.0, true);

  delay(50);
  */
}

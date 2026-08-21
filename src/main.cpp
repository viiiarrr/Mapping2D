#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "Sensor.h"
#include "StepperMotor.h"

// =====================
// KONFIGURASI WIFI & UDP
// =====================
const char* ssid = "rytz";         // <-- ISI NAMA HOTSPOT HP ANDA
const char* password = "admin12345"; // <-- ISI PASSWORD HOTSPOT HP ANDA
const char* laptop_ip = "192.168.137.1";           // IP Laptop Anda (dari hotspot)
const int udp_port = 5005;

WiFiUDP udp;
 
// =====================
// KONFIGURASI PIN
// =====================
const int trigPins[NUM_SENSOR] = {4, 5, 18, 19, 21, 22, 23, 25};
const int echoPins[NUM_SENSOR] = {34, 35, 32, 33, 26, 27, 14, 13};

#define STEP_PIN 16
#define DIR_PIN  17
#define ENABLE_PIN 12

// =====================
// INISIALISASI OBJEK
// =====================
Sensor ultrasonicArray(trigPins, echoPins);
StepperMotor stepper(STEP_PIN, DIR_PIN, ENABLE_PIN, 200, 800);

void setup() {
  Serial.begin(115200);

  // Inisialisasi Wi-Fi
  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected! IP ESP32: " + WiFi.localIP().toString());

  // Inisialisasi sensor dan stepper
  ultrasonicArray.begin();
  stepper.begin();
}

void loop() {
  // 1. BACA SENSOR BERGILIRAN
  ultrasonicArray.readAll();

  // 2. KUMPULKAN DATA KE DALAM STRING (DENGAN SIMULASI DUMMY RUANGAN)
  float current_angle = stepper.getAngle();
  
  // Jika motor belum dipasang dan tidak berputar, mari kita simulasikan sudutnya berputar
  static float simulated_angle = 0.0;
  static bool direction = true;
  if (current_angle == 0) { 
     simulated_angle += (direction ? 5.0 : -5.0);
     if (simulated_angle >= 50.0) direction = false;
     if (simulated_angle <= 0.0) direction = true;
     current_angle = simulated_angle;
  }

  String data_sensor = String(current_angle, 1) + ",";
  for (int i = 0; i < NUM_SENSOR; i++) {
    // ---- MODE SIMULASI RUANGAN SEGITIGA ----
    float actual_angle_deg = fmod((current_angle + (i * 45.0)), 360.0);
    
    // Simulasi dinding ruangan berbentuk segitiga sama sisi dengan jarak 150cm ke dinding terdekat
    float W = 150.0; 
    float dummy_distance = 400.0;
    
    // Segitiga memiliki 3 dinding. Kita hitung jarak pantulan berdasarkan 3 arah normal dinding (90, 210, 330 derajat)
    if (actual_angle_deg >= 30.0 && actual_angle_deg < 150.0) {
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

  // (Opsional) Tetap tampilkan di Serial Monitor laptop untuk debugging jika dicolok kabel
  Serial.println(data_sensor);

  // 3. GERAKKAN STEPPER
  stepper.step(5, true);

  delay(50);
}
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
const char* laptop_ip = "10.159.38.194";           // IP Laptop Anda (dari hotspot)
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

  // 2. KUMPULKAN DATA KE DALAM STRING
  String data_sensor = String(stepper.getAngle(), 1) + ",";
  for (int i = 0; i < NUM_SENSOR; i++) {
    data_sensor += String(ultrasonicArray.getDistance(i), 1);
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
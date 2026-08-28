#include "Sensor.h"
#include "ServoMotor.h"
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// =====================
// KONFIGURASI WIFI & UDP
// =====================
const char *ssid     = "rytz";
const char *password = "admin12345";
const char *laptop_ip = "192.168.137.1";
const int   udp_port  = 5005;

WiFiUDP udp;

// =====================
// KONFIGURASI PIN SENSOR
// =====================
const int trigPins[NUM_SENSOR] = {19, 5, 4, 23, 22, 25, 27, 12};
const int echoPins[NUM_SENSOR] = {18, 35, 34, 32, 33, 26, 14, 13};

// =====================
// HASIL KALIBRASI SERVO
// =====================
// CW  : 110° dalam 2 detik = 55 deg/s
// CCW : 90°  dalam 2 detik = 45 deg/s
#define SERVO_PIN          21
#define SERVO_SPEED_CW     55.0   // deg/s hasil kalibrasi
#define SERVO_SPEED_CCW    45.0   // deg/s hasil kalibrasi

// Step pemetaan: 5° per langkah
// 360° / 5° = 72 langkah x 8 sensor = 576 titik per putaran
#define STEP_DEG           5.0

// Waktu tunggu setelah servo berhenti sebelum sensor dibaca (ms)
// Beri cukup waktu agar getaran servo mereda
#define SETTLE_DELAY_MS    150

// =====================
// OBJEK
// =====================
Servo360Motor servo(SERVO_PIN, SERVO_SPEED_CW, SERVO_SPEED_CCW);
Sensor ultrasonicArray(trigPins, echoPins);

float currentAngle = 0.0;   // Sudut platform saat ini (0-359°)
int   stepCount    = 0;      // Hitungan langkah dalam 1 putaran
const int TOTAL_STEPS = (int)(360.0 / STEP_DEG); // = 72

void bacaDanKirim() {
  ultrasonicArray.readAll();

  // Format: sudut_platform,jarak1,...,jarak8
  String out = String(currentAngle, 1) + ",";
  for (int i = 0; i < NUM_SENSOR; i++) {
    float d = ultrasonicArray.getDistance(i);
    if (d == -1.0) d = 0.0;
    out += String(d, 1);
    if (i < NUM_SENSOR - 1) out += ",";
  }

  if (WiFi.status() == WL_CONNECTED) {
    udp.beginPacket(laptop_ip, udp_port);
    udp.print(out);
    udp.endPacket();
  }

  Serial.println("["  + String(stepCount) + "/" + String(TOTAL_STEPS) +
                 "] " + String(currentAngle, 1) + "deg | " + out);
}

void setup() {
  Serial.begin(115200);

  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);
  int att = 0;
  while (WiFi.status() != WL_CONNECTED && att < 20) {
    delay(500); Serial.print("."); att++;
  }
  Serial.println(WiFi.status() == WL_CONNECTED
    ? "\nWi-Fi OK: " + WiFi.localIP().toString()
    : "\nWi-Fi GAGAL. Lanjut tanpa WiFi...");

  ultrasonicArray.begin();
  servo.begin();   // Servo berhenti dulu
  delay(1500);     // Tunggu servo benar-benar diam
  servo.resetAngle();
  currentAngle = 0.0;
  stepCount    = 0;

  Serial.println("=== MULAI PEMETAAN 360 DERAJAT ===");
  Serial.println("Step: " + String(STEP_DEG) + " deg | Total: " + String(TOTAL_STEPS) + " langkah");
}

bool mappingSelesai = false;

void loop() {
  if (mappingSelesai) {
    delay(1000);
    return;
  }

  Serial.println("=== MULAI PEMETAAN 360 DERAJAT (CONTINUOUS) ===");
  
  // Hitung waktu yang dibutuhkan untuk 1 putaran penuh (360 derajat)
  unsigned long sweepDurationMs = (360.0 / SERVO_SPEED_CW) * 1000.0;
  unsigned long startTime = millis();
  
  // Mulai putar servo
  servo.rotateCW();
  
  while (millis() - startTime <= sweepDurationMs) {
    // 1. Hitung sudut saat ini berdasarkan waktu berlalu (Time-based dead reckoning)
    float elapsedTimeSec = (millis() - startTime) / 1000.0;
    currentAngle = elapsedTimeSec * SERVO_SPEED_CW;
    
    // 2. Baca sensor & kirim UDP secepat mungkin saat sedang berputar
    bacaDanKirim();
  }
  
  // Putaran selesai, hentikan servo
  servo.stop();
  mappingSelesai = true;
  
  Serial.println("=== 1 PUTARAN SELESAI. MAP DIKUNCI. ===");
}

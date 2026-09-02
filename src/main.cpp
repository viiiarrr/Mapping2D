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
// KONFIGURASI HOMING
// =====================
#define HOMING_PIN         15
volatile unsigned long sweepStartTime = 0;
unsigned long sweepDurationMsCW = 0;
unsigned long sweepDurationMsCCW = 0;

enum MotorState { DIR_CW, DIR_CCW };
MotorState currentState = DIR_CW;
unsigned long stateStartTime = 0;

// =====================
// OBJEK
// =====================
Servo360Motor servo(SERVO_PIN, SERVO_SPEED_CW, SERVO_SPEED_CCW);
Sensor ultrasonicArray(trigPins, echoPins);

float currentAngle = 0.0;   // Sudut platform saat ini (0-359°)

void IRAM_ATTR homingISR() {
  // Debounce sederhana 500ms agar tidak double trigger saat menyentuh switch
  if (millis() - sweepStartTime > 500) {
    sweepStartTime = millis();
  }
}

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

  Serial.println("Sudut: " + String(currentAngle, 1) + "deg | " + out);
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
  
  // Konfigurasi Homing
  pinMode(HOMING_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(HOMING_PIN), homingISR, FALLING);
  sweepDurationMsCW = (unsigned long)((360.0 / SERVO_SPEED_CW) * 1000.0);
  sweepDurationMsCCW = (unsigned long)((360.0 / SERVO_SPEED_CCW) * 1000.0);
  
  servo.begin();   // Servo berhenti dulu
  delay(1500);     // Tunggu servo benar-benar diam
  servo.resetAngle();
  currentAngle = 0.0;

  Serial.println("=== MULAI PEMETAAN BOLAK-BALIK (2x KANAN, 2x KIRI) ===");
  stateStartTime = millis();
  sweepStartTime = millis();
  currentState = DIR_CW;
  servo.rotateCW();
}

void loop() {
  unsigned long timeInState = millis() - stateStartTime;
  
  if (currentState == DIR_CW) {
    // Cek apakah sudah 2 putaran (2 * sweepDurationMsCW)
    if (timeInState >= 2 * sweepDurationMsCW) {
      Serial.println(">> Berbalik arah ke KIRI (CCW)");
      currentState = DIR_CCW;
      
      // Beri jeda sejenak agar piringan tidak membal/rusak akibat inersia mendadak
      servo.stop();
      delay(500);
      
      stateStartTime = millis();
      sweepStartTime = millis();
      servo.rotateCCW();
      return;
    }
    
    // Hitung sudut saat ini berdasarkan waktu berlalu (modulo waktu 1 putaran CW)
    unsigned long timeElapsed = (millis() - sweepStartTime) % sweepDurationMsCW;
    currentAngle = ((float)timeElapsed / sweepDurationMsCW) * 360.0;
    
  } else {
    // Cek apakah sudah 2 putaran (2 * sweepDurationMsCCW)
    if (timeInState >= 2 * sweepDurationMsCCW) {
      Serial.println(">> Berbalik arah ke KANAN (CW)");
      currentState = DIR_CW;
      
      // Beri jeda sejenak agar piringan tidak membal/rusak akibat inersia mendadak
      servo.stop();
      delay(500);
      
      stateStartTime = millis();
      sweepStartTime = millis();
      servo.rotateCW();
      return;
    }
    
    // Hitung sudut saat ini (berjalan mundur dari 360 ke 0)
    unsigned long timeElapsed = (millis() - sweepStartTime) % sweepDurationMsCCW;
    currentAngle = 360.0 - (((float)timeElapsed / sweepDurationMsCCW) * 360.0);
  }
  
  // Baca sensor & kirim UDP secara konstan
  bacaDanKirim();
  
  // Jeda sangat singkat untuk stabilitas pengiriman UDP
  delay(20);
}

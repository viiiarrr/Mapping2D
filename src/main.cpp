#include "Sensor.h"
#include "ServoMotor.h"
#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// =====================
// KONFIGURASI WIFI & UDP
// =====================
const char *ssid      = "rytz";
const char *password  = "admin12345";
const char *laptop_ip = "192.168.137.1";
const int   udp_port  = 5005;
WiFiUDP udp;

// =====================
// KONFIGURASI PIN SENSOR
// =====================
const int trigPins[NUM_SENSOR] = {19, 5, 4, 23, 22, 25, 27, 12};
const int echoPins[NUM_SENSOR] = {18, 35, 34, 32, 33, 26, 14, 13};

// =====================
// SERVO
// =====================
#define SERVO_PIN       21
#define SERVO_SPEED_CW  55.0
#define SERVO_SPEED_CCW 45.0

// =====================
// HOMING
// =====================
#define HOMING_PIN 15
volatile unsigned long sweepStartTime = 0;

// =====================
// IMU — PIN I2C (hasil scan)
// =====================
#define I2C_SDA 16
#define I2C_SCL 17
#define MPU     0x68

// =====================
// OBJEK
// =====================
Servo360Motor servo(SERVO_PIN, SERVO_SPEED_CW, SERVO_SPEED_CCW);
Sensor ultrasonicArray(trigPins, echoPins);

// =====================
// STATE ARAH SERVO
// =====================
enum MotorState { DIR_CW, DIR_CCW };
MotorState currentState = DIR_CW;
float sweepStartYaw = 0;   // Yaw saat mulai sweep
#define SWEEP_DEG 720.0    // 2 putaran penuh = 720°

// =====================
// VARIABEL IMU
// =====================
float gyroZ_offset = 0;
float yaw          = 0;
float prevTime     = 0, currTime = 0, elapsedTime = 0;
float currentAngle = 0;

// =====================
// KALIBRASI GYRO Z
// Harus dilakukan saat alat DATAR & DIAM
// =====================
void calibrateGyroZ() {
    Serial.println("[IMU] Kalibrasi GyroZ... Jangan gerakkan alat!");
    long sum = 0;
    for (int i = 0; i < 300; i++) {
        Wire.beginTransmission(MPU);
        Wire.write(0x47);  // GYRO_ZOUT_H
        Wire.endTransmission(false);
        Wire.requestFrom(MPU, 2);
        int16_t raw = Wire.read() << 8 | Wire.read();
        sum += raw;
        delay(10);
    }
    gyroZ_offset = (float)sum / 300.0 / 131.0;
    yaw = 0;  // Reset yaw setelah kalibrasi
    Serial.print("[IMU] GyroZ offset: ");
    Serial.print(gyroZ_offset, 4);
    Serial.println(" deg/s  — Kalibrasi selesai!");
}

// =====================
// UPDATE YAW dari IMU
// =====================
void updateYaw() {
    prevTime    = currTime;
    currTime    = millis();
    elapsedTime = (currTime - prevTime) / 1000.0;

    Wire.beginTransmission(MPU);
    Wire.write(0x47);  // GYRO_ZOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU, 2);
    int16_t rawZ = Wire.read() << 8 | Wire.read();

    float gyroZ = (float)rawZ / 131.0 - gyroZ_offset;

    // Dead-band: noise kecil di bawah 0.8 deg/s diabaikan
    if (abs(gyroZ) < 0.8) gyroZ = 0;

    yaw += gyroZ * elapsedTime;
    currentAngle = yaw;
}

void IRAM_ATTR homingISR() {
    if (millis() - sweepStartTime > 500) {
        sweepStartTime = millis();
    }
}

void bacaDanKirim() {
    updateYaw();
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

    Serial.print("YAW: "); Serial.print(currentAngle, 2);
    Serial.print(" deg | "); Serial.println(out);
}

void setup() {
    Serial.begin(115200);

    // WiFi
    Serial.print("Connecting to Wi-Fi");
    WiFi.begin(ssid, password);
    int att = 0;
    while (WiFi.status() != WL_CONNECTED && att < 20) {
        delay(500); Serial.print("."); att++;
    }
    Serial.println(WiFi.status() == WL_CONNECTED
        ? "\nWi-Fi OK: " + WiFi.localIP().toString()
        : "\nWi-Fi GAGAL. Lanjut tanpa WiFi...");

    // Sensor ultrasonik
    ultrasonicArray.begin();

    // Homing switch
    pinMode(HOMING_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(HOMING_PIN), homingISR, FALLING);

    // IMU
    Wire.begin(I2C_SDA, I2C_SCL);
    delay(200);
    Wire.beginTransmission(MPU);
    Wire.write(0x6B);
    Wire.write(0x00);  // Wake up MPU6050
    Wire.endTransmission(true);
    delay(100);
    calibrateGyroZ();

    // Servo
    servo.begin();
    delay(1500);
    servo.resetAngle();

    currTime = millis();

    Serial.println("=== MULAI PEMETAAN — SERVO BERPUTAR ===");
    sweepStartTime = millis();
    servo.rotateCW();
}

void loop() {
    // Update yaw dari IMU
    updateYaw();

    // Pakai abs agar berlaku untuk CW (yaw negatif) maupun CCW (yaw positif)
    float yawTraveled = abs(yaw - sweepStartYaw);

    if (yawTraveled >= SWEEP_DEG) {
        if (currentState == DIR_CW) {
            Serial.println(">> 2 Putaran CW selesai — Berbalik ke CCW");
            servo.stop();
            delay(500);
            sweepStartYaw = yaw;  // Catat titik awal sweep baru (TIDAK reset yaw)
            currentState  = DIR_CCW;
            servo.rotateCCW();
        } else {
            Serial.println(">> 2 Putaran CCW selesai — Berbalik ke CW");
            servo.stop();
            delay(500);
            sweepStartYaw = yaw;  // Catat titik awal sweep baru (TIDAK reset yaw)
            currentState  = DIR_CW;
            servo.rotateCW();
        }
        return;
    }

    // Baca sensor & kirim
    ultrasonicArray.readAll();
    currentAngle = yaw;

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

    Serial.print(currentState == DIR_CW ? "[CW] " : "[CCW] ");
    Serial.print("YAW: "); Serial.print(currentAngle, 1);
    Serial.print(" | Traveled: "); Serial.print(yawTraveled, 1);
    Serial.print(" | "); Serial.println(out);

    delay(20);
}

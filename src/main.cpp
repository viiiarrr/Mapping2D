#include <Arduino.h>
#include "Sensor.h"
#include "StepperMotor.h"

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

  // Inisialisasi sensor dan stepper
  ultrasonicArray.begin();
  stepper.begin();
}

void loop() {
  // 1. BACA SENSOR BERGILIRAN
  ultrasonicArray.readAll();

  // 2. KIRIM DATA KE RASPI
  // format: angle,d1,d2,...,d8
  Serial.print(stepper.getAngle(), 1);
  Serial.print(",");

  for (int i = 0; i < NUM_SENSOR; i++) {
    Serial.print(ultrasonicArray.getDistance(i), 1);

    if (i < NUM_SENSOR - 1) {
      Serial.print(",");
    }
  }
  Serial.println();

  // 3. GERAKKAN STEPPER
  stepper.step(5, true);

  delay(50);
}
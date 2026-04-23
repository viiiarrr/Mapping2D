#include <Arduino.h>

#define NUM_SENSOR 8

// =====================
// PIN ULTRASONIK
// =====================
int trigPins[NUM_SENSOR] = {4, 5, 18, 19, 21, 22, 23, 25};
int echoPins[NUM_SENSOR] = {34, 35, 32, 33, 26, 27, 14, 13};

float distanceVal[NUM_SENSOR];

// =====================
// PIN STEPPER
// =====================
#define STEP_PIN 16
#define DIR_PIN  17
#define ENABLE_PIN 13   // optional (boleh dihapus kalau tidak pakai)

// =====================
// PARAMETER STEPPER
// =====================
#define STEPS_PER_REV 200        // tergantung motor (biasanya 200)
#define STEP_DELAY_US 800        // kecepatan motor

int currentStep = 0;
float currentAngle = 0;

// =====================
// FUNGSI ULTRASONIK
// =====================
float readUltrasonic(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long startTime = micros();

  // tunggu echo HIGH
  while (digitalRead(echoPin) == LOW) {
    if (micros() - startTime > 30000) return -1;
  }

  long echoStart = micros();

  // tunggu echo LOW
  while (digitalRead(echoPin) == HIGH) {
    if (micros() - echoStart > 30000) return -1;
  }

  long duration = micros() - echoStart;

  float dist = duration * 0.0343 / 2;

  return dist;
}

// =====================
// STEPPER FUNCTION
// =====================
void stepMotor(int steps, bool direction) {
  digitalWrite(DIR_PIN, direction);

  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(STEP_DELAY_US);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(STEP_DELAY_US);

    currentStep++;
    if (currentStep >= STEPS_PER_REV) currentStep = 0;
  }

  // hitung sudut
  currentAngle = (currentStep * 360.0) / STEPS_PER_REV;
}

// =====================
// SETUP
// =====================
void setup() {
  Serial.begin(115200);

  // ultrasonic
  for (int i = 0; i < NUM_SENSOR; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  // stepper
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);

  digitalWrite(ENABLE_PIN, LOW); // aktifkan driver
}

// =====================
// LOOP
// =====================
void loop() {

  // =====================
  // 1. BACA SEMUA SENSOR
  // =====================
  for (int i = 0; i < NUM_SENSOR; i++) {
    distanceVal[i] = readUltrasonic(trigPins[i], echoPins[i]);
    delay(30); // hindari interferensi
  }

  // =====================
  // 2. OUTPUT DATA
  // format: angle,d1,d2,...,d8
  // =====================
  Serial.print(currentAngle, 1);
  Serial.print(",");

  for (int i = 0; i < NUM_SENSOR; i++) {
    Serial.print(distanceVal[i], 1);
    if (i < NUM_SENSOR - 1) Serial.print(",");
  }
  Serial.println();

  // =====================
  // 3. GERAKKAN STEPPER
  // =====================
  stepMotor(5, true);  // 5 step tiap loop

  delay(50);
}
#ifndef SERVO_MOTOR_H
#define SERVO_MOTOR_H

#include <Arduino.h>
#include <ESP32Servo.h>

class Servo360Motor {
private:
    int servoPin;
    Servo myServo;
    
    // Variabel untuk estimasi sudut (karena servo 360 tidak punya sensor posisi)
    float currentAngle; 
    float speedDegreesPerSec; 

public:
    // Constructor
    Servo360Motor(int pin, float estimatedSpeed = 180.0) {
        servoPin = pin;
        currentAngle = 0.0;
        // Asumsi kasar kecepatan servo: misal 180 derajat per detik.
        // Anda HARUS mengkalibrasi nilai ini dengan stopwatch & busur derajat
        // agar visualisasi 2D nya bisa mendekati akurat.
        speedDegreesPerSec = estimatedSpeed; 
    }
    
    void begin() {
        // Alokasi timer wajib untuk ESP32Servo
        ESP32PWM::allocateTimer(0);
        ESP32PWM::allocateTimer(1);
        ESP32PWM::allocateTimer(2);
        ESP32PWM::allocateTimer(3);

        myServo.setPeriodHertz(50);
        // Range 500-2400us adalah standar umum untuk MG996R
        myServo.attach(servoPin, 500, 2400);
        stop();
    }
    
    // Putar penuh searah jarum jam (Clockwise)
    void rotateCW() {
        myServo.write(0);
    }

    // Putar penuh berlawanan arah jarum jam (Counter-Clockwise)
    void rotateCCW() {
        myServo.write(180);
    }

    // Berhenti
    void stop() {
        // Nilai 90 adalah titik berhenti standar servo 360.
        // Jika servo masih mendengung/berputar sangat pelan, ubah ke 89 atau 91.
        myServo.write(90); 
    }
    
    // Fungsi pengganti "step" pada Stepper Motor. 
    // Menggunakan delay waktu untuk mengestimasi pergerakan sudut.
    // PENTING: Metode ini tidak akan seakurat Stepper Motor asli.
    void moveAngle(float targetAngleDelta, bool direction) {
        // Hitung berapa lama servo harus menyala untuk mencapai target sudut
        float timeToMoveMs = (targetAngleDelta / speedDegreesPerSec) * 1000.0;
        
        if (direction) {
            rotateCW();
            currentAngle += targetAngleDelta;
        } else {
            rotateCCW();
            currentAngle -= targetAngleDelta;
        }
        
        // Biarkan servo berputar selama waktu yang dihitung, lalu paksa berhenti
        delay(timeToMoveMs);
        stop();
        
        // Normalisasi sudut agar selalu berada di antara 0 - 359 derajat
        if (currentAngle >= 360.0) currentAngle = fmod(currentAngle, 360.0);
        if (currentAngle < 0.0) currentAngle = 360.0 + fmod(currentAngle, 360.0);
    }
    
    float getAngle() {
        return currentAngle;
    }

    void resetAngle() {
        currentAngle = 0.0;
    }
};

#endif // SERVO_MOTOR_H

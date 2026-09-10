#ifndef IMU_H
#define IMU_H

#include <Wire.h>
#include <Arduino.h>

class ImuSensor {
private:
    static constexpr uint8_t MPU = 0x68;
    float AccX, AccY, AccZ;
    float GyroX, GyroY, GyroZ;
    float accAngleX, accAngleY, gyroAngleX, gyroAngleY;
    float roll, pitch, yaw;
    float AccErrorX, AccErrorY, GyroErrorX, GyroErrorY, GyroErrorZ;
    float elapsedTime, currentTime, previousTime;
    int sdaPin, sclPin;

    void calculate_IMU_error() {
        int c = 0;
        AccErrorX = 0;
        AccErrorY = 0;
        GyroErrorX = 0;
        GyroErrorY = 0;
        GyroErrorZ = 0;

        // Read accelerometer values 200 times
        while (c < 200) {
            Wire.beginTransmission(MPU);
            Wire.write(0x3B);
            Wire.endTransmission(false);
            Wire.requestFrom(MPU, (uint8_t)6);
            AccX = (Wire.read() << 8 | Wire.read()) / 16384.0;
            AccY = (Wire.read() << 8 | Wire.read()) / 16384.0;
            AccZ = (Wire.read() << 8 | Wire.read()) / 16384.0;
            
            AccErrorX = AccErrorX + ((atan((AccY) / sqrt(pow((AccX), 2) + pow((AccZ), 2))) * 180 / PI));
            AccErrorY = AccErrorY + ((atan(-1 * (AccX) / sqrt(pow((AccY), 2) + pow((AccZ), 2))) * 180 / PI));
            c++;
            delay(2);
        }
        AccErrorX = AccErrorX / 200;
        AccErrorY = AccErrorY / 200;
        
        c = 0;
        // Read gyro values 200 times
        while (c < 200) {
            Wire.beginTransmission(MPU);
            Wire.write(0x43);
            Wire.endTransmission(false);
            Wire.requestFrom(MPU, (uint8_t)6);
            
            GyroX = (Wire.read() << 8 | Wire.read()) / 131.0;
            GyroY = (Wire.read() << 8 | Wire.read()) / 131.0;
            GyroZ = (Wire.read() << 8 | Wire.read()) / 131.0;
            
            GyroErrorX = GyroErrorX + GyroX;
            GyroErrorY = GyroErrorY + GyroY;
            GyroErrorZ = GyroErrorZ + GyroZ;
            c++;
            delay(2);
        }
        GyroErrorX = GyroErrorX / 200;
        GyroErrorY = GyroErrorY / 200;
        GyroErrorZ = GyroErrorZ / 200;
        
        Serial.println("IMU Calibration Done!");
        Serial.print("AccErrX: "); Serial.print(AccErrorX);
        Serial.print(" | AccErrY: "); Serial.println(AccErrorY);
        Serial.print("GyroErrX: "); Serial.print(GyroErrorX);
        Serial.print(" | GyroErrY: "); Serial.println(GyroErrorY);
    }

public:
    ImuSensor(int sda = 16, int scl = 17) : sdaPin(sda), sclPin(scl) {
        roll = 0;
        pitch = 0;
        yaw = 0;
        gyroAngleX = 0;
        gyroAngleY = 0;
        AccErrorX = 0;
        AccErrorY = 0;
        GyroErrorX = 0;
        GyroErrorY = 0;
        GyroErrorZ = 0;
        currentTime = 0;
        previousTime = 0;
    }

    void begin() {
        Wire.begin(sdaPin, sclPin);
        
        Wire.beginTransmission(MPU);
        Wire.write(0x6B); // Power management register
        Wire.write(0x00); // Wake up MPU6050
        Wire.endTransmission(true);

        // Configure Accelerometer (+/- 8g)
        Wire.beginTransmission(MPU);
        Wire.write(0x1C);
        Wire.write(0x10);
        Wire.endTransmission(true);
        
        // Configure Gyro (+/- 1000deg/s)
        Wire.beginTransmission(MPU);
        Wire.write(0x1B);
        Wire.write(0x10);
        Wire.endTransmission(true);
        delay(20);

        calculate_IMU_error();
        delay(20);

        currentTime = millis();
    }

    void update() {
        // Read Accelerometer
        Wire.beginTransmission(MPU);
        Wire.write(0x3B);
        Wire.endTransmission(false);
        Wire.requestFrom(MPU, (uint8_t)6);
        
        AccX = (Wire.read() << 8 | Wire.read()) / 16384.0;
        AccY = (Wire.read() << 8 | Wire.read()) / 16384.0;
        AccZ = (Wire.read() << 8 | Wire.read()) / 16384.0;
        
        accAngleX = (atan(AccY / sqrt(pow(AccX, 2) + pow(AccZ, 2))) * 180 / PI) - AccErrorX;
        accAngleY = (atan(-1 * AccX / sqrt(pow(AccY, 2) + pow(AccZ, 2))) * 180 / PI) - AccErrorY;

        // Calculate time elapsed
        previousTime = currentTime;
        currentTime = millis();
        elapsedTime = (currentTime - previousTime) / 1000.0;

        // Read Gyroscope
        Wire.beginTransmission(MPU);
        Wire.write(0x43);
        Wire.endTransmission(false);
        Wire.requestFrom(MPU, (uint8_t)6);
        
        GyroX = (Wire.read() << 8 | Wire.read()) / 131.0;
        GyroY = (Wire.read() << 8 | Wire.read()) / 131.0;
        GyroZ = (Wire.read() << 8 | Wire.read()) / 131.0;

        // Correct gyro with error values
        GyroX = GyroX - GyroErrorX;
        GyroY = GyroY - GyroErrorY;
        GyroZ = GyroZ - GyroErrorZ;

        // Dead-band: noise kecil diabaikan (mengikuti logika awal main.cpp)
        if (abs(GyroZ) < 0.8) GyroZ = 0;

        gyroAngleX = gyroAngleX + GyroX * elapsedTime;
        gyroAngleY = gyroAngleY + GyroY * elapsedTime;
        yaw        = yaw        + GyroZ * elapsedTime;

        // Complementary filter
        roll  = 0.96 * gyroAngleX + 0.04 * accAngleX;
        pitch = 0.96 * gyroAngleY + 0.04 * accAngleY;
    }

    float getRoll()  { return roll; }
    float getPitch() { return pitch; }
    float getYaw()   { return yaw; }
};

#endif // IMU_H

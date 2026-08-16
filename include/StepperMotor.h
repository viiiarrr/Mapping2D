#ifndef STEPPER_MOTOR_H
#define STEPPER_MOTOR_H

#include <Arduino.h>

class StepperMotor {
private:
    int stepPin;
    int dirPin;
    int enablePin;
    
    int stepsPerRev;
    int stepDelayUs;
    
    int currentStep;
    float currentAngle;

public:
    StepperMotor(int stepP, int dirP, int enP, int sPerRev = 200, int dUs = 800) {
        stepPin = stepP;
        dirPin = dirP;
        enablePin = enP;
        stepsPerRev = sPerRev;
        stepDelayUs = dUs;
        
        currentStep = 0;
        currentAngle = 0.0;
    }
    
    void begin() {
        pinMode(stepPin, OUTPUT);
        pinMode(dirPin, OUTPUT);
        pinMode(enablePin, OUTPUT);

        digitalWrite(enablePin, LOW); // aktifkan driver
    }
    
    void step(int steps, bool direction) {
        digitalWrite(dirPin, direction);

        for (int i = 0; i < steps; i++) {
            digitalWrite(stepPin, HIGH);
            delayMicroseconds(stepDelayUs);
            digitalWrite(stepPin, LOW);
            delayMicroseconds(stepDelayUs);

            currentStep++;
            if (currentStep >= stepsPerRev) {
                currentStep = 0;
            }
        }

        currentAngle = (currentStep * 360.0) / stepsPerRev;
    }
    
    float getAngle() {
        return currentAngle;
    }
};

#endif // STEPPER_MOTOR_H

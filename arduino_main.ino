# include <Arduino.h>
# include "BasicStepperDriver.h"

// The purpose of the arduino is to:
// 1. Receive instructions from raspberry pi
// 2. Execute instructions (move stepper motors)
// 3. Notify raspberry pi when it is done

// Motor steps per revolution. Most steppers are 200
# define MOTOR_STEPS 200
# define RPM 120

// microstep mode
# define MICROSTEPS 16

// RAMPS 1.4 to Arduino Mega

# define X_STEP A0 // X
# define X_DIR A1
# define X_EN 38
# define Y_STEP A6 // Y
# define Y_DIR A7
# define Y_EN A2
# define Z_STEP 26 // E0
# define Z_DIR 28
# define Z_EN 24
# define L_STEP 36// E1
# define L_DIR 34
# define L_EN 30

// how much the motor should move for each step
const int x_steps = 100;
const int y_steps = 100;
const int z_steps = 80;
const int l_steps = 2900; // should be changed once new gears are printed
const int accel = 1000;

BasicStepperDriver x_stepper(MOTOR_STEPS, X_DIR, X_STEP, X_EN);
BasicStepperDriver y_stepper(MOTOR_STEPS, Y_DIR, Y_STEP, Y_EN);
BasicStepperDriver z_stepper(MOTOR_STEPS, Z_DIR, Z_STEP, Z_EN);
BasicStepperDriver l_stepper(MOTOR_STEPS, L_DIR, L_STEP, L_EN);

void setup() {
  Serial.begin(9600); // baud rate
  
  x_stepper.begin(RPM, MICROSTEPS);
  x_stepper.setEnableActiveState(LOW);
  x_stepper.enable();
  x_stepper.setSpeedProfile(z_stepper.LINEAR_SPEED, accel, accel); // acceleration set at this amount due to issues with turning knobs at higher acceleration


  y_stepper.begin(RPM, MICROSTEPS);
  y_stepper.setEnableActiveState(LOW);
  y_stepper.enable();
  y_stepper.setSpeedProfile(z_stepper.LINEAR_SPEED, accel, accel);


  z_stepper.begin(RPM, MICROSTEPS);
  z_stepper.setEnableActiveState(LOW);
  z_stepper.enable();
  z_stepper.setSpeedProfile(z_stepper.LINEAR_SPEED, accel, accel);

  l_stepper.begin(RPM, MICROSTEPS);
  l_stepper.setEnableActiveState(LOW);
  l_stepper.enable();
  l_stepper.setSpeedProfile(z_stepper.LINEAR_SPEED, accel, accel);
  
}

void move_motor(String instruction) {
  // read motor name and direction
  char motor_name = instruction[0];
  char direction = instruction[2];
  
  if (motor_name == 'x') {
    if (direction == '+') {
      x_stepper.move(x_steps);
    }
    else if (direction == '-') {
      x_stepper.move(-1*x_steps);
    }
  }
  else if (motor_name == 'y') {
    if (direction == '+') {
      y_stepper.move(y_steps);
    }
    else if (direction == '-') {
      y_stepper.move(-1*y_steps);
    }
  }
  else if (motor_name == 'z') {
    if (direction == '+') {
      z_stepper.move(z_steps);
    }
    else if (direction == '-') {
      z_stepper.move(-1*z_steps);
    }
  }
  else if (motor_name == 'l') {
    if (direction == '+') {
      l_stepper.move(l_steps);
    }
    else if (direction == '-') {
      l_stepper.move(-1*l_steps);
    }
  }
  Serial.println("Done");
}

void loop() {
  // wait for raspberry pi to send instruction
  if (Serial.available() > 0) {
    // read instruction
    String instruction = Serial.readStringUntil('\n');
    // execute instruction
    move_motor(instruction);
  }
}


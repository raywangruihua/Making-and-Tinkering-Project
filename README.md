As part of a summer-long multidisciplinary engineering project, my group and I designed and built an automatic microscope. We named it the Autoscope. 

The Autoscope zooms in on the specimen placed within it and captures a clear image, then either identifies the cell in the specimen or takes additional images to store in a dataset. This dataset is used to fine-tune a lightweight pre-trained machine learning model, enabling the Autoscope to learn to identify more cell types in the future.

The Autoscope is made up of a microscope, which is fitted with stepper motors and an Arducam Hawkeye camera. The stepper motors are connected to an Arduino Mega with Ramps 1.4, which receives instructions from a Raspberry Pi 5 to move the motors.

Shown below is the Autoscope setup.
<img src="https://github.com/user-attachments/assets/cbe82beb-ff4f-4d17-aad4-15c488782f29" width="200"/>

Close-up of the 2 controllers.
<img src="https://github.com/user-attachments/assets/b3e0eb6c-d14f-4887-a5f2-2a92b9e2d1aa" width="200"/>

The main code is stored on the Raspberry Pi; however, due to limitations in local computation capabilities, some code is executed on GoogleColab. This enables the use of GPUs, which accelerate many of the machine learning components in our project.

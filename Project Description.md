# Introduction
As part of a summer-long multidisciplinary project, my group and I designed and built an automatic microscope. We named it the Autoscope. 

The Autoscope is made up of several components: A microscope, Raspberry Pi 5, Arduino Mega with Ramps 1.4, stepper motors, Arducam Hawkeye camera, and 3D printed parts to integrate the parts together.

Shown below is the Autoscope setup.
</br>
<p align=center>
  <img src="https://github.com/user-attachments/assets/cbe82beb-ff4f-4d17-aad4-15c488782f29" width="400"/>
</p>

Close-up of the Raspberry Pi and Arduino.
</br>
<p align=center>
  <img src="https://github.com/user-attachments/assets/b3e0eb6c-d14f-4887-a5f2-2a92b9e2d1aa" width="400"/>
</p>

# Working Principle
The Autoscope works as follows:
1. Place a sample under the microscope, ensure that some part of the sample can be seen under the microscope.
2. Execute the main python file on the Raspberry Pi through a keyboard, mouse and monitor setup.
3. Input the starting objective lens used.
4. Wait for the Autoscope to focus and scan the sample.
5. Authenticate your Google account.
6. Run the cell_counter script on GoogleColab and enter "done" into the Raspberry Pi when finished.
7. Wait for the Autoscope to reach the maximum zoom objective lens and focus on the sample.
   A final image will be shown when the Autoscope is finished.
8. Choose whether to take a final picture of the sample and upload the image for cell identification through cell_identifier.
   OR
   Enter data collection mode where the Autoscope will take a large number of images.
9. When data collection is completed, run the model finetuner in the cell_identifier to train the model to recognise the new cell type.

The physical operation of the Autoscope can be seen in the video in this repository.

# Comments
The cell_counter and cell_identifier is run on GoogleColab due to limitations in computing power of the Raspberry Pi 5. Additionally, GoogleColab also provides the use of GPUs which accelerate the run time of both scripts.

Future features to be added can be a GUI interface and packaging the code into an .exe file.

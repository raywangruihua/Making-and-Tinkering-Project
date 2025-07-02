A small machine learning project that was done as part of my Making and Tinkering module at NTU. This project consists of 2 parts: Data processing and Finetuning.

In data processing, sample images (Commonly brightfield microscopy images) are given to Cellpose-SAM, which identifies cells within the image and creates masks. The cells are then cropped out and saved into the training data directory.

In finetuning, I finetune the EfficientNetLite-B0 model on cell data. This model was chosen to be suitable for mobile devices, and I plan to run it on a Raspberry Pi.

The final product is to be used in conjunction with a Raspberry Pi and Aruduino Mega + Ramps 1.4 controlling a microscopy via stepper motors attached to knobs. The goal is to automate the sample image taking process, as well as give some data processing functionality, while keeping costs low, so that school laboratories can make use of the deivce.

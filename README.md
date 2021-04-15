# spot-robot


## Pre requisites


apt install python3-smbus


pip3 install -r requirements.txt

Add ubuntu user to i2c group
usermod -a -G i2c ubuntu


Build and run
python3 src/gyro.py
python3 src/spot.py




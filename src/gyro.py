from mpu6050 import mpu6050
from math import atan2

from posix_ipc import MessageQueue, O_CREX, unlink_message_queue


from time import sleep, time

MAX_MSG=5
LOOP_TIME_S=0.05

class SpotGyro():

    def __init__(self):
        try:
            unlink_message_queue("/gyro")
        except:
            pass

        self.mqueue=MessageQueue('/gyro', flags=O_CREX, max_messages=MAX_MSG)

        try:
            self.gyro=mpu6050(0x68)
        except:
            raise Exception("Could not connect to Gyroscope MPU6050")

        self.angleFront=0.
        self.angleSide=0.

    def get_position(self):

        try:
            accelval = self.gyro.get_accel_data()
            gyroval = self.gyro.get_gyro_data()

            self.angleFront=0.80*(self.angleFront+float(gyroval['y'])*0.01/131) + 0.20*atan2(accelval['x'],accelval['z'])*180/3.14159
            self.angleSide=0.80*(self.angleSide+float(gyroval['x'])*0.01/131) + 0.20*atan2(accelval['y'],accelval['z'])*180/3.14159

            if self.mqueue.current_messages >= MAX_MSG:
                self.mqueue.receive()

            self.mqueue.send('{"front":"' + str(self.angleFront) + '","side":"' +  str(self.angleSide) + '","time":"' + str(time()) + '"}')
        
        except Exception:
            pass







if __name__ == "__main__":
    gyro=SpotGyro()

    while True:
        start=time()
        gyro.get_position()
        stop=time()


        if stop-start > LOOP_TIME_S:
            wait=0
        else:
            wait=LOOP_TIME_S-(stop-start)

        sleep(wait)

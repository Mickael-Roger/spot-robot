from posix_ipc import MessageQueue

import time

class Spot():

    def __init__(self):
        self.mqgyro = MessageQueue("/gyro")
        print("TOTO")


    def get_gyro(self):
        msg = self.mqgyro.receive()
        print(msg)


if __name__ == '__main__':

    spot=Spot()


    while True:
        spot.get_gyro()
        time.sleep(1)

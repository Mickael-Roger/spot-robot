from posix_ipc import MessageQueue
import threading

import json

import time


all_run=True

gyro_front = 0.
gyro_side = 0.
gyro_time = 0.
gyro_lock = threading.Lock()

def spotgyro():
    global gyro_front, gyro_side, gyro_time, gyro_time

    mqgyro = MessageQueue("/gyro")

    while all_run:
        try:
            msg = mqgyro.receive()
            msgvalues=json.loads(msg[0])
            gyro_lock.acquire()
            gyro_front=float(msgvalues['front'])
            gyro_side=float(msgvalues['side'])
            gyro_time=float(msgvalues['time'])
            gyro_lock.release()
        except:
            pass


def signal_handler(sig, frame):
    global all_run
    print('Bye Bye')
    all_run=False

if __name__ == '__main__':

    # Create Gyro thread
    gyro_thread = threading.Thread(name='spotgyro', target=spotgyro)
    gyro_thread.setDaemon(True)
    gyro_thread.start()


    while all_run:
        time.sleep(1)
        gyro_lock.acquire()
        print("Front: " + str(gyro_front))
        print("Side : " + str(gyro_side))
        print("Time : " + str(gyro_time))
        gyro_lock.release()


    gyro_thread.join()

from posix_ipc import MessageQueue
import threading

import json

import time


all_run=True

gyro_front = 0.
gyro_side = 0.
gyro_time = 0.
gyro_lock = threading.Lock()

spot_forward=0
spot_backward=0
spot_left=0
spot_right=0
spot_bodyleft=0
spot_bodyright=0
spot_bodyfront=0
spot_bodyback=0
spot_motiontime=0.
spot_motionlock = threading.Lock()


def spotgyro():
    global gyro_front, gyro_side, gyro_time, gyro_lock

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


def spotmotion_reset():
    global spot_forward, spot_backward, spot_left, spot_right,spot_bodyfront, spot_bodyback, spot_bodyleft, spot_bodyright, spot_motiontime, spot_motionlock
    spot_forward=0
    spot_backward=0
    spot_left=0
    spot_right=0
    spot_bodyleft=0
    spot_bodyright=0
    spot_bodyfront=0
    spot_bodyback=0



def spotmotion():
    global spot_forward, spot_backward, spot_left, spot_right,spot_bodyfront, spot_bodyback, spot_bodyleft, spot_bodyright, spot_motiontime, spot_motionlock
    
    mqmotion = MessageQueue("/spotmotion")

    while all_run:
        try:
            msg = mqmotion.receive()
            msgvalues=json.loads(msg[0])
            spot_motionlock.acquire()


            if msgvalues['action'] == 'stop':
                spotmotion_reset()
            elif msgvalues['action'] == 'forward':
                spotmotion_reset()
                spot_forward=1
            elif msgvalues['action'] == 'backward':
                spotmotion_reset()
                spot_backward=1
            elif msgvalues['action'] == 'left':
                spotmotion_reset()
                spot_left=1
            elif msgvalues['action'] == 'right':
                spotmotion_reset()
                spot_right=1
            elif msgvalues['action'] == 'bodyleft':
                spotmotion_reset()
                spot_bodyleft=1
            elif msgvalues['action'] == 'bodyright':
                spotmotion_reset()
                spot_bodyright=1
            elif msgvalues['action'] == 'bodyfront':
                spotmotion_reset()
                spot_bodyfront=1
            elif msgvalues['action'] == 'bodyback':
                spotmotion_reset()
                spot_bodyback=1
            elif msgvalues['action'] == 'wakeup':
                spotmotion_reset()
                print('wakeup')
            elif msgvalues['action'] == 'laydown':
                spotmotion_reset()
                print('laydown')
            spot_motionlock.release()

        except:
            spot_motionlock.acquire()
            spotmotion_reset()
            spot_motionlock.release()


def signal_handler(sig, frame):
    global all_run
    print('Bye Bye')
    all_run=False

if __name__ == '__main__':

    # Create Gyro thread
    gyro_thread = threading.Thread(name='spotgyro', target=spotgyro)
    gyro_thread.setDaemon(True)
    gyro_thread.start()

    # Create Motion thread
    spotmotion_thread = threading.Thread(name='spotmotion', target=spotmotion)
    spotmotion_thread.setDaemon(True)
    spotmotion_thread.start()



    while all_run:
        time.sleep(0.1)
        spot_motionlock.acquire()
        if spot_forward==1:
            print('Forward')
        if spot_backward==1:
            print('Backward')
        if spot_left==1:
            print('Left')
        if spot_right==1:
            print('Right')
        if spot_bodyright==1:
            print('Body Right')
        if spot_bodyleft==1:
            print('Body Left')
        if spot_bodyfront==1:
            print('Body Front')
        if spot_bodyback==1:
            print('Body Back')
        spot_motionlock.release()


    gyro_thread.join()
    potmotion_thread.join()

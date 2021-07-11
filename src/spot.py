from posix_ipc import MessageQueue, BusyError, unlink_message_queue, O_CREX
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
            msg = mqgyro.receive(timeout=1)
            msgvalues=json.loads(msg[0])
            gyro_lock.acquire()
            gyro_front=float(msgvalues['front'])
            gyro_side=float(msgvalues['side'])
            gyro_time=float(msgvalues['time'])
            gyro_lock.release()
        except BusyError: 
            time.sleep(1)
            mqgyro = MessageQueue("/gyro")
        except:
            pass


def spotgamepad_reset():
    global spot_forward, spot_backward, spot_left, spot_right,spot_bodyfront, spot_bodyback, spot_bodyleft, spot_bodyright, spot_motiontime, spot_motionlock
    spot_forward=0
    spot_backward=0
    spot_left=0
    spot_right=0
    spot_bodyleft=0
    spot_bodyright=0
    spot_bodyfront=0
    spot_bodyback=0



def spotgamepad():
    global spot_forward, spot_backward, spot_left, spot_right,spot_bodyfront, spot_bodyback, spot_bodyleft, spot_bodyright, spot_motiontime, spot_motionlock
    
    mqmotion = MessageQueue("/spotgamepad")

    while all_run:
        try:
            msg = mqmotion.receive()
            msgvalues=json.loads(msg[0])
            spot_motionlock.acquire()


            if msgvalues['action'] == 'stop':
                spotgamepad_reset()
            elif msgvalues['action'] == 'forward':
                spotgamepad_reset()
                spot_forward=1
            elif msgvalues['action'] == 'backward':
                spotgamepad_reset()
                spot_backward=1
            elif msgvalues['action'] == 'left':
                spotgamepad_reset()
                spot_left=1
            elif msgvalues['action'] == 'right':
                spotgamepad_reset()
                spot_right=1
            elif msgvalues['action'] == 'bodyleft':
                spotgamepad_reset()
                spot_bodyleft=1
            elif msgvalues['action'] == 'bodyright':
                spotgamepad_reset()
                spot_bodyright=1
            elif msgvalues['action'] == 'bodyfront':
                spotgamepad_reset()
                spot_bodyfront=1
            elif msgvalues['action'] == 'bodyback':
                spotgamepad_reset()
                spot_bodyback=1
            elif msgvalues['action'] == 'wakeup':
                spotgamepad_reset()
                print('wakeup')
            elif msgvalues['action'] == 'laydown':
                spotgamepad_reset()
                print('laydown')
            spot_motionlock.release()

        except:
            spot_motionlock.acquire()
            spotgamepad_reset()
            spot_motionlock.release()


def signal_handler(sig, frame):
    global all_run
    print('Bye Bye')
    all_run=False

if __name__ == '__main__':

    try:
        unlink_message_queue("/spotmotion")
    except:
        pass

    spotmotion=MessageQueue('/spotmotion', flags=O_CREX, max_messages=5)


    # Create Gyro thread
    gyro_thread = threading.Thread(name='spotgyro', target=spotgyro)
    gyro_thread.setDaemon(True)
    gyro_thread.start()

    # Create Gamedpad thread
    spotgamepad_thread = threading.Thread(name='spotgamepad', target=spotgamepad)
    spotgamepad_thread.setDaemon(True)
    spotgamepad_thread.start()



    while all_run:
        time.sleep(0.1)
        spot_motionlock.acquire()
        if spot_forward == 0 and spot_backward == 0 and spot_left == 0 and spot_right == 0 and spot_bodyright == 0 and spot_bodyleft == 0 and spot_bodyfront == 0 and spot_bodyback == 0:
            print('Stop')
            spotmotion.send('{"action":"stop"}')
        elif spot_forward==1:
            print('Forward')
            spotmotion.send('{"action":"forward"}')
        elif spot_backward==1:
            print('Backward')
            spotmotion.send('{"action":"backward"}')
        elif spot_left==1:
            print('Left')
            spotmotion.send('{"action":"left"}')
        elif spot_right==1:
            print('Right')
            spotmotion.send('{"action":"right"}')
        elif spot_bodyright==1:
            print('Body Right')
        elif spot_bodyleft==1:
            print('Body Left')
        elif spot_bodyfront==1:
            print('Body Front')
        elif spot_bodyback==1:
            print('Body Back')
        spot_motionlock.release()

        gyro_lock.acquire()
        print('Gryo : ' + str(gyro_front) + ' ' + str(gyro_side) + ' ' + str(gyro_time))
        gyro_lock.release()


    gyro_thread.join()
    spotgamepad_thread.join()

import threading

from http.server import BaseHTTPRequestHandler, HTTPServer
import sys

from mpu6050 import mpu6050
from math import atan2, acos, cos, sin, asin, degrees, radians, sqrt

import evdev

from time import sleep, time
from adafruit_servokit import ServoKit


FRONT_LEFT=0
FRONT_RIGHT=1
BACK_LEFT=2
BACK_RIGHT=3

BACK_RIGHT_LEG=14
BACK_RIGHT_SHOULDER=12
BACK_RIGHT_FOOT=13

BACK_LEFT_LEG=2
BACK_LEFT_SHOULDER=1
BACK_LEFT_FOOT=0

FRONT_RIGHT_LEG=10
FRONT_RIGHT_SHOULDER=8
FRONT_RIGHT_FOOT=9

FRONT_LEFT_LEG=4
FRONT_LEFT_SHOULDER=5
FRONT_LEFT_FOOT=6

INPUT_DEVICE="/dev/input/event0"


GYRO_CORR_FRONT=2.16
GYRO_CORR_SIDE=-1.1


all_run=True

gyro_front = 0.
gyro_side = 0.
gyro_time = 0.
gyro_lock = threading.Lock()

spot_gamepadmotion=None
spot_gamepadmotionlock = threading.Lock()


def spotgyro():
    global gyro_front, gyro_side, gyro_time, gyro_lock, all_run

    while all_run:

        gyro=None

        while gyro == None:
            try:
                gyro=mpu6050(0x68)
            except:
                raise Exception("Could not connect to Gyroscope MPU6050")

            sleep(1)

        tmp_front = 0
        tmp_side = 0

        for i in range(10):
            accelval = gyro.get_accel_data()
            gyroval = gyro.get_gyro_data()

            tmp_front = tmp_front + atan2(accelval['x'],accelval['z'])*180/3.14159
            tmp_side = tmp_side + atan2(accelval['y'],accelval['z'])*180/3.14159

            sleep(0.1)

        gyro_lock.acquire()
        gyro_front=tmp_front/10 + GYRO_CORR_FRONT
        gyro_side=tmp_side/10 + GYRO_CORR_SIDE
        gyro_time=time()

        print("Initialized: " + str(gyro_front) + " - " + str(gyro_side)) 

        if gyro_lock.locked():
            gyro_lock.release()

        while True:
            try:
                
                accelval = gyro.get_accel_data()
                gyroval = gyro.get_gyro_data()

                nowtime = time()

                gyro_lock.acquire()

                dt = nowtime - gyro_time
                gyro_time = nowtime

                front_accel = atan2(accelval['x'],accelval['z'])*180/3.14159
                side_accel = atan2(accelval['y'],accelval['z'])*180/3.14159

                front_gyro_rate = gyroval['y'] / 131
                side_gyro_rate = gyroval['x'] / 131

                gyro_front = round((0.95 * (gyro_front - GYRO_CORR_FRONT + front_gyro_rate * dt) + 0.05 * front_accel) + GYRO_CORR_FRONT, 2)
                gyro_side = round((0.95 * (gyro_side - GYRO_CORR_SIDE + side_gyro_rate * dt) + 0.05 * side_accel) + GYRO_CORR_SIDE, 2)
                

                #print("RES: " + str(dt) + " - " + str(gyro_front) + " " + str(gyro_side) + " " + str(front_gyro_rate) + " " + str(side_gyro_rate) + " " + str(front_accel) + " " + str(side_accel) )

                if gyro_lock.locked():
                    gyro_lock.release()


            except Exception:
                pass
                if gyro_lock.locked():
                    gyro_lock.release()

            sleep(0.005)






def update_gamepadmotion(event):
    global spot_gamepadmotion, spot_gamepadmotionlock

    spot_gamepadmotionlock.acquire()
    spot_gamepadmotion=event
    spot_gamepadmotionlock.release()

def spotgamepad():
    
    while all_run:

        try:
            gamepad=evdev.InputDevice(INPUT_DEVICE)

            for event in gamepad.read_loop():
                if event.type == evdev.ecodes.EV_ABS:
                    absevent = evdev.categorize(event)

                    # If motion button
                    if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_HAT0Y':
                        code = absevent.event.value

                        if code == -1:
                            update_gamepadmotion('forward')
                        elif code == 1:
                            update_gamepadmotion('backward')
                        else:
                            update_gamepadmotion(None)

                    if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_HAT0X':
                        code = absevent.event.value

                        if code == -1:
                            update_gamepadmotion('left')
                        elif code == 1:
                            update_gamepadmotion('right')
                        else:
                            update_gamepadmotion(None)


                    # If body position joystick
                    if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_X':
                        if absevent.event.value < 128:
                            update_gamepadmotion('bodyleft')
                        elif absevent.event.value > 128:
                            update_gamepadmotion('bodyright')
                        else:
                            update_gamepadmotion(None)

                    if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_Y':
                        if absevent.event.value < 128:
                            update_gamepadmotion('bodyfront')
                        elif absevent.event.value > 128:
                            update_gamepadmotion('bodyback')
                        else:
                            update_gamepadmotion(None)



                    # If camera position joystick
                    if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_Z':
                        print('lateral camera: ' + str(absevent.event.value))

                    if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_RZ':
                        print('front camera: ' + str(absevent.event.value))


                # If action button
                if event.type == evdev.ecodes.EV_KEY:
                    keyevent = evdev.categorize(event)

                    # Laydown
                    if 'BTN_A' in evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code]:
                        if keyevent.event.value == 0:
                            update_gamepadmotion('laydown')

                    # Wake up
                    if 'BTN_Y' in evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code]:
                        if keyevent.event.value == 0:
                            update_gamepadmotion('wakeup')

                    # Move up
                    if 'BTN_TR' in evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code]:
                        if keyevent.event.value == 0:
                            update_gamepadmotion('moveup')

                    # Move down
                    if 'BTN_TL' in evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code]:
                        if keyevent.event.value == 0:
                            update_gamepadmotion('movedown')

                    # Stabilisation
                    if 'BTN_B' in evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code]:
                        if keyevent.event.value == 0:
                            update_gamepadmotion('stable')

                    # Start Servos
                    if evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code] == 'BTN_START':
                        if keyevent.event.value == 0:
                            update_gamepadmotion('startservos')

                    # Stop Servos
                    if evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code] == 'BTN_SELECT':
                        if keyevent.event.value == 0:
                            update_gamepadmotion('stopservos')

            

        except:
            update_gamepadmotion(None)






def signal_handler(sig, frame):
    global all_run
    print('Bye Bye')
    all_run=False



class Spot():

    def __init__(self):
        self.corrections = [3, 0, 3, 0, -7, -3, 4, 0, 5, 3, 7, 0, 0, 0, 0, 0]
        self.positions = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

        self.desired_high = None
        self.desired_front = 0
        self.desired_side = 0

        self.servos = ServoKit(channels=16)

        for i in range(16):
            self.servos.servo[i].set_pulse_width_range(500 , 2500)


        # Start position
        self.movepart(FRONT_LEFT_SHOULDER, 85)
        self.movepart(BACK_RIGHT_SHOULDER, 85)
        self.movepart(FRONT_RIGHT_SHOULDER, 85)
        self.movepart(BACK_LEFT_SHOULDER, 85)

        self.movepart(BACK_RIGHT_FOOT, 47)
        self.movepart(BACK_LEFT_FOOT, 47)
        self.movepart(FRONT_RIGHT_FOOT, 47)
        self.movepart(FRONT_LEFT_FOOT, 47)
        
        self.movepart(BACK_LEFT_LEG, 169)
        self.movepart(BACK_RIGHT_LEG, 169)
        self.movepart(FRONT_LEFT_LEG, 169)
        self.movepart(FRONT_RIGHT_LEG, 169)




    def movepart(self, part, position):

        if position + self.corrections[part] > 180:
            position=180 - self.corrections[part]
        elif position + self.corrections[part] < 0:
            position=0 - self.corrections[part]

        if part == FRONT_LEFT_FOOT or part == BACK_LEFT_FOOT or part == BACK_LEFT_LEG or part == FRONT_LEFT_LEG or part == FRONT_LEFT_SHOULDER or part == BACK_RIGHT_SHOULDER:
            self.positions[part] = position
            self.servos.servo[part].angle = position + self.corrections[part]
        
        elif part == FRONT_RIGHT_FOOT or part == BACK_RIGHT_FOOT or part == FRONT_RIGHT_LEG or part == BACK_RIGHT_LEG or part == FRONT_RIGHT_SHOULDER or part == BACK_LEFT_SHOULDER:
            self.positions[part] = position 
            self.servos.servo[part].angle = 180 - (position + self.corrections[part])


    def wakeup(self):

        global spot_gamepadmotion

        self.desired_high = 15

        self.moveleg([FRONT_RIGHT, FRONT_LEFT, BACK_RIGHT, BACK_LEFT] , [15 - spot.leghigh(FRONT_RIGHT), 15 - spot.leghigh(FRONT_LEFT) , 15 - spot.leghigh(BACK_RIGHT), 15 - spot.leghigh(BACK_LEFT)])

        self.desired_front = 0
        self.desired_side = 0

        spot_gamepadmotionlock.acquire()
        spot_gamepadmotion='stop'
        spot_gamepadmotionlock.release()


    def laydown(self):

        global spot_gamepadmotion
        
        self.desired_high = 5
        self.desired_front = 0
        self.desired_side = 0

        self.moveleg([FRONT_RIGHT, FRONT_LEFT, BACK_RIGHT, BACK_LEFT] , [5 - spot.leghigh(FRONT_RIGHT), 5 - spot.leghigh(FRONT_LEFT) , 5 - spot.leghigh(BACK_RIGHT), 5 - spot.leghigh(BACK_LEFT)])


    def stop(self):
        print("Stop")

    def forward(self):

        print("forward")



    def backward(self):
        print('Backward')


    def right(self):
        print("right")


    def left(self):
        print("left")


    def bodyleft(self):
        print('Body Left')

    def bodyright(self):
        print('Body Right')

    def bodyfront(self):
        self.desired_front = self.desired_front + 1
        self.gyroposition(front_pos=self.desired_front, side_pos=self.desired_side)
        print('Body Front' + str(self.desired_front))

    def bodyback(self):
        self.desired_front = self.desired_front - 1
        self.gyroposition(front_pos=self.desired_front, side_pos=self.desired_side)
        print('Body Back' + str(self.desired_front))

    def bodyupdown(self, move):
        self.desired_high = self.desired_high + move
        self.moveleg([FRONT_RIGHT, FRONT_LEFT, BACK_RIGHT, BACK_LEFT] , [self.desired_high - spot.leghigh(FRONT_RIGHT), self.desired_high - spot.leghigh(FRONT_LEFT) , self.desired_high - spot.leghigh(BACK_RIGHT), self.desired_high - spot.leghigh(BACK_LEFT)])


    # To improve
    #   Better movement identication (do not only used 0.1 or 0.2), do not sleep at the end, ...
    def gyroposition(self, front_pos=0, side_pos=0):
        global gyro_front, gyro_time, gyro_side, gyro_lock

        while all_run:

            gyro_lock.acquire()
            gytime=gyro_time
            front=gyro_front
            side=gyro_side
            if gyro_lock.locked():
                gyro_lock.release()

            if (time() - gytime) < 0.1:
                if abs(front - front_pos) > 1 or abs(side - side_pos) > 1:

                    frontleft=self.leghigh(FRONT_LEFT)
                    frontright=self.leghigh(FRONT_RIGHT)
                    backleft=self.leghigh(BACK_LEFT)
                    backright=self.leghigh(BACK_RIGHT)

                    frontlen = max([frontleft, frontright])
                    backlen = max([backleft, backright])
                    rightlen = max([backright, frontright])
                    leftlen = max([frontleft, backleft])

                    if front < (front_pos - 1):
                        
                        if (abs(frontlen - self.desired_high) > abs(backlen - self.desired_high)) or backlen > self.desired_high:
                            if backlen > (self.desired_high + 0.5):
                                self.moveleg([BACK_RIGHT, BACK_LEFT] , [-0.1, -0.1])
                                self.moveleg([FRONT_RIGHT, FRONT_LEFT] , [-0.2, -0.2])
                            else:
                                self.moveleg([FRONT_RIGHT, FRONT_LEFT] , [-0.1, -0.1])
                        else:
                            if frontlen > (self.desired_high + 0.5):
                                self.moveleg([FRONT_RIGHT, FRONT_LEFT] , [-0.1, -0.1])
                            
                            self.moveleg([BACK_RIGHT, BACK_LEFT] , [0.1, 0.1])


                    if front > (front_pos + 1):
                        
                        if (abs(frontlen - self.desired_high) < abs(backlen - self.desired_high)) or frontlen < self.desired_high:
                            if backlen > (self.desired_high + 0.5):
                                self.moveleg([BACK_RIGHT, BACK_LEFT] , [-0.1, -0.1])

                            self.moveleg([FRONT_RIGHT, FRONT_LEFT] , [0.1, 0.1])
                        else:
                            if frontlen > (self.desired_high + 0.5):
                                self.moveleg([FRONT_RIGHT, FRONT_LEFT] , [-0.1, -0.1])
                                self.moveleg([BACK_RIGHT, BACK_LEFT] , [-0.2, -0.2])
                            else:
                                self.moveleg([BACK_RIGHT, BACK_LEFT] , [-0.1, -0.1])


                    if side > (side_pos + 1):

                        if (abs(leftlen - self.desired_high) > abs(rightlen - self.desired_high)) or rightlen > self.desired_high:
                            if rightlen > (self.desired_high + 0.5):
                                self.moveleg([FRONT_RIGHT, BACK_RIGHT] , [-0.1, -0.1])

                            self.moveleg([FRONT_LEFT, BACK_LEFT] , [0.1, 0.1])
                        else:
                            
                            if leftlen > (self.desired_high + 0.5):
                                self.moveleg([FRONT_LEFT, BACK_LEFT] , [-0.1, -0.1])
                                self.moveleg([FRONT_RIGHT, BACK_RIGHT] , [-0.2, -0.2])
                            else:
                                self.moveleg([FRONT_RIGHT, BACK_RIGHT] , [-0.1, -0.1])



                    if side < (side_pos - 1):

                        if (abs(leftlen - self.desired_high) < abs(rightlen - self.desired_high)) or leftlen > self.desired_high:
                            if leftlen > (self.desired_high + 0.5):
                                self.moveleg([FRONT_LEFT, BACK_LEFT] , [-0.1, -0.1])

                            self.moveleg([FRONT_RIGHT, BACK_RIGHT] , [0.1, 0.1])
                        else:
                            if rightlen > (self.desired_high + 0.5):
                                self.moveleg([FRONT_LEFT, BACK_LEFT] , [-0.2, -0.2])
                                self.moveleg([FRONT_RIGHT, BACK_RIGHT] , [-0.1, -0.1])
                            else:
                                self.moveleg([FRONT_LEFT, BACK_LEFT] , [-0.1, -0.1])


                else:
                    break

                sleep(0.01)

    def leghigh(self, leg):
        if leg == FRONT_LEFT:
            foot = FRONT_LEFT_FOOT
            leg = FRONT_LEFT_LEG
        elif leg == FRONT_RIGHT:
            foot = FRONT_RIGHT_FOOT
            leg = FRONT_RIGHT_LEG
        elif leg == BACK_LEFT:
            foot = BACK_LEFT_FOOT
            leg = BACK_LEFT_LEG
        elif leg == BACK_RIGHT:
            foot = BACK_RIGHT_FOOT
            leg = BACK_RIGHT_LEG

        return sqrt(303.25 - (2 * 148.5 * cos(radians(self.positions[foot]))))


    # To improve
    #   Catch errors, ...
    def moveleg(self, legs=[], motions=[]):

        while all( v != 0 for v in motions):

            for idx, oneleg in enumerate(legs):

                if oneleg == FRONT_LEFT:
                    foot = FRONT_LEFT_FOOT
                    leg = FRONT_LEFT_LEG
                elif oneleg == FRONT_RIGHT:
                    foot = FRONT_RIGHT_FOOT
                    leg = FRONT_RIGHT_LEG
                elif oneleg == BACK_LEFT:
                    foot = BACK_LEFT_FOOT
                    leg = BACK_LEFT_LEG
                elif oneleg == BACK_RIGHT:
                    foot = BACK_RIGHT_FOOT
                    leg = BACK_RIGHT_LEG

                actual_high = self.leghigh(oneleg)

                if abs(motions[idx]) > 0.2:

                    if motions[idx] > 0:
                        new_high = actual_high + 0.2
                        motions[idx] = motions[idx] - 0.2
                    else:
                        new_high = actual_high - 0.2
                        motions[idx] = motions[idx] + 0.2

                else:
                    new_high = actual_high + motions[idx]
                    motions[idx] = 0             


                self.movepart(foot, degrees(acos((303.25 - pow(new_high,2)) / 297)))
                self.movepart(leg, 90 + degrees(acos((pow(new_high,2) - 61.5) / (22*new_high))))


            sleep(0.0005)



    def stable(self):
        self.gyroposition(front_pos=0, side_pos=0)

class MyDebugServer(BaseHTTPRequestHandler):
    def do_GET(self):
        global gyro_front, gyro_side, gyro_time, gyro_lock, all_run

        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes('{"gyro": {"front": ' + str(gyro_front) + ', "side": ' + str(gyro_side) + '}}', 'utf-8'))


if __name__ == '__main__':


    # Create Gyro thread
    gyro_thread = threading.Thread(name='spotgyro', target=spotgyro)
    gyro_thread.setDaemon(True)
    gyro_thread.start()

    # Create Gamedpad thread
    spotgamepad_thread = threading.Thread(name='spotgamepad', target=spotgamepad)
    spotgamepad_thread.setDaemon(True)
    spotgamepad_thread.start()

    spot=Spot()

    # Debug server
    if len(sys.argv) > 1 and sys.argv[1] == '--dev':
        webServer = HTTPServer(('192.168.1.26', 8080), MyDebugServer)
        print("Debug Server started http://%s:%s" % ('192.168.1.26', 8080))
        debug_thread = threading.Thread(name='webServer.serve_forever', target=webServer.serve_forever)
        debug_thread.setDaemon(True)
        debug_thread.start()



        spot.laydown()
        sleep(5)

        spot.wakeup()
        sleep(3)

        spot.laydown()
        sleep(5)

        spot.wakeup()
        sleep(5)

        spot.laydown()
        sleep(1)

        for j in range(2):
            spot.moveleg([FRONT_RIGHT, FRONT_LEFT, BACK_RIGHT, BACK_LEFT] , [20 - spot.leghigh(FRONT_RIGHT), 20 - spot.leghigh(FRONT_LEFT) , 20 - spot.leghigh(BACK_RIGHT), 20 - spot.leghigh(BACK_LEFT)])
            spot.moveleg([FRONT_RIGHT, FRONT_LEFT, BACK_RIGHT, BACK_LEFT] , [5 - spot.leghigh(FRONT_RIGHT), 5 - spot.leghigh(FRONT_LEFT) , 5 - spot.leghigh(BACK_RIGHT), 5 - spot.leghigh(BACK_LEFT)])

        sleep(5)

        spot.desired_high = 15
        spot.moveleg([FRONT_RIGHT, FRONT_LEFT, BACK_RIGHT, BACK_LEFT] , [15 - spot.leghigh(FRONT_RIGHT), 15 - spot.leghigh(FRONT_LEFT) , 15 - spot.leghigh(BACK_RIGHT), 15 - spot.leghigh(BACK_LEFT)])
        sleep(3)

        #while True:
            #spot.stable()
        #    spot.gyroposition(front_pos=-15, side_pos=0)


        sleep(100000)


    while all_run:
        sleep(0.1)
        spot_gamepadmotionlock.acquire()
        action=spot_gamepadmotion
        spot_gamepadmotionlock.release()

        gyro_lock.acquire()
        print("Front : " + str(gyro_front) + " - " + "Side : " + str(gyro_side))
        if gyro_lock.locked():
            gyro_lock.release()

        if action == 'stop':
            spot.stop()
        elif action == 'stable':
            spot.stable()
        elif action == 'forward':
            spot.forward()
            update_gamepadmotion('stop')
        elif action == 'backward':
            spot.backward()
            update_gamepadmotion('stop')
        elif action == 'left':
            spot.left()
            update_gamepadmotion('stop')
        elif action == 'right':
            spot.right()
            update_gamepadmotion('stop')
        elif action == 'bodyright':
            spot.bodyright()
            update_gamepadmotion('stop')
        elif action == 'bodyleft':
            spot.bodyleft()
            update_gamepadmotion('stop')
        elif action == 'bodyfront':
            spot.bodyfront()
            update_gamepadmotion('stop')
        elif action == 'bodyback':
            spot.bodyback()
            update_gamepadmotion('stop')
        elif action == 'wakeup':
            spot.wakeup()
            update_gamepadmotion('stop')
        elif action == 'laydown':
            spot.laydown()
            update_gamepadmotion('stop')
        elif action == 'moveup':
            spot.bodyupdown(1)
            update_gamepadmotion('stop')
        elif action == 'movedown':
            spot.bodyupdown(-1)
            update_gamepadmotion('stop')
        


    gyro_thread.join()
    spotgamepad_thread.join()

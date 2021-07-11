from time import time
from adafruit_servokit import ServoKit


BACK_RIGHT_LEG=3
BACK_RIGHT_SHOULDER=1
BACK_RIGHT_FOOT=0

BACK_LEFT_LEG=14
BACK_LEFT_SHOULDER=12
BACK_LEFT_FOOT=13

FRONT_RIGHT_LEG=10
FRONT_RIGHT_SHOULDER=8
FRONT_RIGHT_FOOT=9

FRONT_LEFT_LEG=4
FRONT_LEFT_SHOULDER=5
FRONT_LEFT_FOOT=6



class SpotMotion():

    def __init__(self):
        self.corrections = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.positions = [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]

        self.servos = ServoKit(channels=16)

        for i in range(16):
            self.servos.servo[i].set_pulse_width_range(500 , 2500)


    def movepart(self, part, position):

        if part == FRONT_RIGHT_FOOT or part == BACK_RIGHT_FOOT or part == BACK_LEFT_LEG or part == BACK_LEFT_LEG or part == FRONT_LEFT_SHOULDER or part == BACK_RIGHT_SHOULDER:
            self.positions[part] == position
            self.servos.servo[part].angle = position
        
        elif part == FRONT_LEFT_FOOT or part == BACK_LEFT_FOOT or part == FRONT_RIGHT_LEG or part == BACK_RIGHT_LEG or part == FRONT_RIGHT_SHOULDER or part == BACK_LEFT_SHOULDER:
            self.positions[part] == position + self.corrections[part]
            self.servos.servo[part].angle = 180 - position + self.corrections[part]




# function init 
def init():

    


# function main 
def main():

    pcaScenario();


# function pcaScenario 
def pcaScenario():
    """Scenario to test servo"""
    
    pca.servo[BACK_RIGHT_FOOT].angle = 90 + CORRECTION[BACK_RIGHT_FOOT]
    pca.servo[BACK_LEFT_FOOT].angle = 90 + CORRECTION[BACK_LEFT_FOOT]
    pca.servo[FRONT_RIGHT_FOOT].angle = 90 + CORRECTION[FRONT_RIGHT_FOOT]
    pca.servo[FRONT_LEFT_FOOT].angle = 90 + CORRECTION[FRONT_LEFT_FOOT]

    time.sleep(1)




if __name__ == '__main__':
    init()
    main()

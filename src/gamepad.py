import evdev
from posix_ipc import MessageQueue, O_CREX, unlink_message_queue

from time import sleep, time

INPUT_DEVICE="/dev/input/event0"

MAX_MSG=5

laydown_button='BTN_A'
wakeup_button='BTN_Y'




class SpotGamepad():

    def __init__(self):
        try:
            unlink_message_queue("/spotgamepad")
            unlink_message_queue("/cameramotion")
        except:
            pass

        self.motionqueue=MessageQueue('/spotgamepad', flags=O_CREX, max_messages=MAX_MSG)
        self.cameraqueue=MessageQueue('/cameramotion', flags=O_CREX, max_messages=MAX_MSG)

        # Initialize Gamepad
        self.gamepad=evdev.InputDevice(INPUT_DEVICE)
        

    def read_event(self):
        for event in self.gamepad.read_loop():
            if event.type == evdev.ecodes.EV_ABS:
                absevent = evdev.categorize(event)

                # If motion button
                if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_HAT0Y':
                    code = absevent.event.value

                    if code == -1:
                        self.send_msg('spotgamepad', '{"action":"forward","time":"' + str(time()) + '"}')
                    elif code == 1:
                        self.send_msg('spotgamepad', '{"action":"backward","time":"' + str(time()) + '"}')
                    else:
                        self.send_msg('spotgamepad', '{"action":"stop","time":"' + str(time()) + '"}')

                if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_HAT0X':
                    code = absevent.event.value

                    if code == -1:
                        self.send_msg('spotgamepad', '{"action":"left","time":"' + str(time()) + '"}')
                    elif code == 1:
                        self.send_msg('spotgamepad', '{"action":"right","time":"' + str(time()) + '"}')
                    else:
                        self.send_msg('spotgamepad', '{"action":"stop","time":"' + str(time()) + '"}')


                # If body position joystick
                if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_X':
                    if absevent.event.value < 128:
                        self.send_msg('spotgamepad', '{"action":"bodyleft","time":"' + str(time()) + '"}')
                    elif absevent.event.value > 128:
                        self.send_msg('spotgamepad', '{"action":"bodyright","time":"' + str(time()) + '"}')
                    else:
                        self.send_msg('spotgamepad', '{"action":"stop","time":"' + str(time()) + '"}')

                if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_Y':
                    if absevent.event.value < 128:
                        self.send_msg('spotgamepad', '{"action":"bodyfront","time":"' + str(time()) + '"}')
                    elif absevent.event.value > 128:
                        self.send_msg('spotgamepad', '{"action":"bodyback","time":"' + str(time()) + '"}')
                    else:
                        self.send_msg('spotgamepad', '{"action":"stop","time":"' + str(time()) + '"}')



                # If camera position joystick
                if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_Z':
                    print('lateral camera: ' + str(absevent.event.value))

                if evdev.ecodes.bytype[absevent.event.type][absevent.event.code] == 'ABS_RZ':
                    print('front camera: ' + str(absevent.event.value))


            # If action button
            if event.type == evdev.ecodes.EV_KEY:
                keyevent = evdev.categorize(event)

                # Laydown
                if laydown_button in evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code]:
                    if keyevent.event.value == 0:
                        self.send_msg('spotgamepad', '{"action":"laydown","time":"' + str(time()) + '"}')

                # Wake up
                if wakeup_button in evdev.ecodes.bytype[keyevent.event.type][keyevent.event.code]:
                    if keyevent.event.value == 0:
                        self.send_msg('spotgamepad', '{"action":"wakeup","time":"' + str(time()) + '"}')




    def send_msg(self, queue, msg):

        if self.cameraqueue.current_messages >= MAX_MSG:
            self.cameraqueue.receive()

        if self.motionqueue.current_messages >= MAX_MSG:
            self.motionqueue.receive()

        if queue == 'spotgamepad':
            self.motionqueue.send(msg)

        elif queue == 'cameramotion':
            self.cameraqueue.send(msg)


if __name__ == "__main__":

    gamepad=SpotGamepad()
    gamepad.read_event()


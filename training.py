import airsim
import PathFollower
import pygame
import threading
import time
import csv
import winsound
from transforms3d import euler
import playsound


class DriveSimulator:
    START_X = -175.0
    START_Y = -925000.0
    START_Z = 0.0

    lock = threading.Lock()

    autoControl = False

    end_sim = False

    isHardBraking = False
    afterHardBrake = False
    already_passed = False

    def __init__(self):
        pygame.init()
        self.t = pygame.time.Clock()
        print("Number of Devices ", pygame.joystick.get_count())

        self.d = pygame.joystick.Joystick(0) # initializes G-27 console OR Xbox controller
        self.d.init()

        # self.d2 = pygame.joystick.Joystick(0) # initializes G-27 console OR Xbox controller
        # self.d2.init()

        # establish connection to AirSim
        self.client = airsim.CarClient()
        self.client.confirmConnection()
        self.client.enableApiControl(False)
        self.car_controls = airsim.CarControls()

        self.warning_played = False

        # reset vehicle to starting position if it isn't already there
        self.client.reset()

        # create path follower object and give it a path to follow
        self.pf = PathFollower.PathFollower(self.START_X, self.START_Y, self.START_Z, 18.78) # 18.78 m/s = 42 mph
        with open("training_path.csv", "w+") as outfile:
            path = csv.writer(outfile)
            for i in range(int(self.START_Y), int(self.START_Y) + 60000, 100):
                path.writerow([self.START_X, i])
        self.pf.input_path_csv("training_path.csv")
        self.wp_idx = 0

        self.minimumCarStateDict =  {
                                     'x' : 0.0,
                                     'y' : 0.0,
                                     'speed' : 0.0,
                                     'orientation' : 0.0
                                    }
        self.update_minimumCarState()


    def control_switching(self): # This function checks the controller inputs periodically
        while not self.end_sim and pygame.event.get(pygame.QUIT) == []:
            xy = pygame.event.get(pygame.JOYAXISMOTION)

            if xy != []:
                xy_data = []
                for c in range(0, self.d.get_numaxes()):
                    xy_data += [str(round(self.d.get_axis(c), 1))]
                if self.autoControl == True:
                    if abs(float(xy_data[0])) > 0.15 or float(xy_data[3]) < 0.7: # if steering or pressing the brake pedal...
                        self.lock.acquire()
                        self.client.enableApiControl(False)
                        self.lock.release()
                        self.autoControl = False
            upbutton = pygame.event.get(pygame.JOYBUTTONUP)
            for button in upbutton:
                if button.button == 7 and self.autoControl == False:
                    self.lock.acquire()
                    self.client.enableApiControl(True)
                    self.lock.release()
                    self.autoControl = True
                    flw = threading.Thread(target=DriveSimulator.call_follow_path, args=(self,))
                    flw.start()


                if button.button == 0:
                    if self.autoControl == True:
                        self.lock.acquire()
                        self.client.enableApiControl(False)
                        self.lock.release()
                        self.autoControl = False

            time.sleep(0.01)

    def update_minimumCarState(self):
        self.lock.acquire()
        self.minimumCarStateDict['x'] = self.client.getCarState().kinematics_estimated.position.x_val
        self.minimumCarStateDict['y'] = self.client.getCarState().kinematics_estimated.position.y_val
        self.minimumCarStateDict['speed'] = self.client.getCarState().speed
        orientationQuaternion = [self.client.getCarState().kinematics_estimated.orientation.w_val,
                                 self.client.getCarState().kinematics_estimated.orientation.x_val,
                                 self.client.getCarState().kinematics_estimated.orientation.y_val,
                                 self.client.getCarState().kinematics_estimated.orientation.z_val]
        self.lock.release()
        eulerAngles = euler.quat2euler(orientationQuaternion)
        self.minimumCarStateDict['orientation'] = eulerAngles[2]

    def next_waypoint(self):
        x = self.minimumCarStateDict['x']
        y = self.minimumCarStateDict['y']

        h = self.pf.points[self.wp_idx]['x']
        k = self.pf.points[self.wp_idx]['y']
        r = 6
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def create_point(self, x, y):
        return (((x - self.START_X) / 100), ((y - self.START_Y) / 100))

    def obs_too_close(self):
        x = self.minimumCarStateDict['x']
        y = self.minimumCarStateDict['y']

        obs = self.create_point(-170, -884530)

        h = obs[0]
        k = obs[1]
        r = 40
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def obs_close(self):
        x = self.minimumCarStateDict['x']
        y = self.minimumCarStateDict['y']

        obs = self.create_point(-170, -884530)

        h = obs[0]
        k = obs[1]
        r = 90
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def hard_brake(self):
        brk = threading.Thread(target=DriveSimulator.brake_sound, args=(self,))
        brk.start()
        self.car_controls.handbrake = True
        self.car_controls.brake = 1.0 # regular brake also actuated
        self.lock.acquire()
        self.client.setCarControls(self.car_controls)
        self.lock.release()
        self.isHardBraking = True

    def play_feedback_warning(self):
        if self.autoControl and not self.warning_played:
            wrn =  threading.Thread(target=DriveSimulator.play_warning, args=(self,))
            wrn.start()
            self.warning_played = True

    def call_follow_path(self):
        while self.autoControl and not self.isHardBraking:
            self.lock.acquire()
            car_state = self.client.getCarState()
            car_controls = self.pf.follow_path(self.wp_idx, car_state)
            self.client.setCarControls(car_controls)
            self.lock.release()
            time.sleep(0.01)

    def brake_sound(self):
        if not self.afterHardBrake:
            winsound.PlaySound('./audios/brake_tone', winsound.SND_FILENAME)

    def play_warning(self):
        if not self.warning_played:
            playsound.playsound('./audios/stopped_vehicle_ahead_take_control_now.mp3', True)

    def simulate(self):
        while not self.end_sim:
            self.update_minimumCarState()

            # if it is hard braking, wait till speed goes close to zero to give back control to the driver
            if abs(self.minimumCarStateDict['speed']) < 0.01 and self.isHardBraking == True:
                self.lock.acquire()
                self.client.enableApiControl(False)
                self.lock.release()
                self.autoControl = False
                self.isHardBraking = False
                self.afterHardBrake = True

            if self.next_waypoint():
                if self.wp_idx == len(self.pf.points) - 1:
                    self.end_sim = True
                else:
                    self.wp_idx += 1

            if self.autoControl and self.obs_too_close() and not self.isHardBraking and not self.already_passed:
                self.hard_brake()
                self.already_passed = True

            if self.obs_close():
                self.play_feedback_warning()

        self.lock.acquire()
        self.client.enableApiControl(False)
        self.client.simPause(True)
        self.lock.release()
        self.autoControl = False
        print("Training Completed")

    def start_simulation(self):
        sim = threading.Thread(target=DriveSimulator.simulate, args=(self,))
        sim.start()

        cs = threading.Thread(target=DriveSimulator.control_switching, args=(self,))
        cs.start()


ds = DriveSimulator()
ds.start_simulation()

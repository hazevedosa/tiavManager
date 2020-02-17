import PathFollower
import airsim
import pygame
import threading
import math
import winsound
import time
import datetime
import pygame
import csv

class DriveSimulator:

    CONDITIONS = [("fog", "control"), ("fog", "FP"), ("fog", "FN"), ("fog", "FPFN")]
    weathIdx = '2'
    reliability_list = ['control', 'FP', 'FN', 'FPFN']

    autoControl = False
    braking = False
    lock = threading.Lock()
    track_begin = True
    vehLane = "Right"
    emergency_brakecCounter = 0

    peblFilePath = ''

    obs_lane = "N/A"
    alarm_type = "N/A"
    glob_ttc = 0
    msg_time = "N/A"
    las_msg= ""

    obstacle_index = 1
    l2dist = 435 #??
    chos_Flag = False
    chos_displayed = 0

    # starting coordinates of the vehicle in Unreal
    START_X = -175.0
    START_Y = -925000.0
    START_Z = 50.0

    CRUISE_V = 20.0
    ENABLE_V = 16.0



    def __init__(self):

        # set up controllers
        pygame.init()
        self.t = pygame.time.Clock()
        print("Number of Devices ", pygame.joystick.get_count())
        self.d = pygame.joystick.Joystick(0)
        self.d.init()

        # establish connection to AirSim
        self.client = airsim.CarClient()
        self.client.confirmConnection()
        self.client.enableApiControl(False)
        self.car_controls = airsim.CarControls()

        # reset vehicle to starting position if it isn't already there
        self.client.reset()

        self.client.simEnableWeather(True)
        self.client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.25)

        # create path follower object and give it a path to follow
        self.pf = PathFollower.PathFollower(self.client, self.START_X, self.START_Y, self.START_Z, 14.7523) # 14.7523 m/s = 33 mph
        self.create_straight_path()
        self.pf.input_path_csv("path.csv")
        #self.pf.input_path_csv("figure_eight.csv") # once there is a real path built, use that

        # there are probably other things to put in here but this is a start
        ## such as: all data stuff

    def set_reliability_conditions(self):
        self.condition = self.CONDITIONS[[self.subj_id % 4][0] - 1]
        self.reliability = self.condition[1]
        print("reliability condition = ", self.reliability)
        if self.reliability == self.reliability_list[0]:
            self.map_basis = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        if self.reliability == self.reliability_list[1]:
            self.map_basis = [1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1]
        if self.reliability == self.reliability_list[2]:
            self.map_basis = [1, -1, -1, 1, -1, -1, 1, -1, 1, 1, 1, 1]
        if self.reliability == self.reliability_list[3]:
            self.map_basis = [1, 0, -1, 1, -1, 1, 1, 0, 1, 1, 1, 1]

    def create_straight_path(self):
        with open("path.csv", "w") as csvfile:
            file = csv.writer(csvfile)
            for i in range(-924000, 180000, 250):
                file.writerow([-175, i])
        self.wp_idx = 0

        self.obstacles = []
        for i in range(-924000, 180000, 100000):
            self.obstacles.append([-175, i])
        self.obs_idx = 0


    def control_switching(self):
        while pygame.event.get(pygame.QUIT) == []:
            xy = pygame.event.get(pygame.JOYAXISMOTION)

            if xy != []:
                xy_data = []
                for c in range(0, self.d.get_numaxes()):
                    xy_data += [str(round(self.d.get_axis(c), 1))]
                if self.autoControl == True and self.braking == False:
                    if abs(float(xy_data[0])) > 0.15 or float(xy_data[3]) < 0.7:
                        self.lock.acquire()
                        self.client.enableApiControl(False)
                        self.autoControl = False
                        #uwp = threading.Thread(target=self.update_wp_man_mode)
                        #uwp.start()
                        self.lock.release()

            upbutton = pygame.event.get(pygame.JOYBUTTONUP)
            for button in upbutton:
                if button.button == 7 and self.autoControl == False:
                    self.lock.acquire()
                    self.client.enableApiControl(True)
                    self.autoControl = True
                    self.lock.release()
                    pft = threading.Thread(target=DriveSimulator.call_follow_path, args=(self,))
                    pft.start()
                    #self.lock.release()
            time.sleep(0.01)
        # continue looking at this

    def call_follow_path(self):
        self.lock.acquire()
        while self.autoControl:
            car_state = self.client.getCarState()
            self.car_controls = self.pf.follow_path(self.wp_idx, car_state)
            self.client.setCarControls(self.car_controls)
            self.lock.release()
            time.sleep(0.1)
            self.lock.acquire()

        self.car_controls.throttle = 0
        self.car_controls.steering = 0
        self.car_controls.handbrake = True
        self.client.setCarControls(self.car_controls)

    def next_waypoint(self):
        x = self.client.getCarState().kinematics_estimated.position.x_val
        y = self.client.getCarState().kinematics_estimated.position.y_val
        h = self.pf.points[self.wp_idx]['x']
        k = self.pf.points[self.wp_idx]['y']
        r = 6
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def obs_close(self):
        x = self.client.getCarState().kinematics_estimated.position.x_val
        y = self.client.getCarState().kinematics_estimated.position.y_val
        h = self.obstacles[self.obs_idx][0]
        k = self.obstacles[self.obs_idx][1]
        r = 100
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def obs_too_close(self):
        x = self.client.getCarState().kinematics_estimated.position.x_val
        y = self.client.getCarState().kinematics_estimated.position.y_val
        h = self.obstacles[self.obs_idx][0]
        k = self.obstacles[self.obs_idx][1]
        r = 10
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    '''
    def update_wp_man_mode(self):
        self.lock.acquire()
        while not self.client.isApiControlEnabled():
            if self.next_waypoint():
                self.wp_idx += 1
            self.lock.release()
            time.sleep(0.1)
            self.lock.acquire()
    '''

    def course_finished(self):
        return False

    def hard_brake(self):
        self.brake_sound()
        self.autoControl = False
        self.car_controls.brake = True
        self.client.setCarControls(self.car_controls)
        self.client.enableApiControl(False)

    def calculate_ttc(self):
        pass

    def play_feedback(self):
        if self.autoControl:
            if self.obs_close():
                wrn = threading.Thread(target=DriveSimulator.obs_spotted, args=(self,))
                wrn.start()
                con = threading.Thread(target=DriveSimulator.action_sound, args=(self,))
                con.start()
            '''
            if self.obs_too_close():
                snd = threading.Thread(target=DriveSimulator.brake_sound, args=(self,))
                snd.start()
                self.autoControl = False
                self.client.car_controls.brake = True
                self.client.setCarControls(car_controls)
                self.client.enableApiControl(False)
            '''

    def engage_auto(self):
        winsound.PlaySound("please_enable_autonomy_now", winsound.SND_FILENAME)
        #self.last_msg = "please_enable_autonomy_now"
        #self.msg_time = datetime.datetime.now().strftime("%I:%M:%S:%f %p %m-%d-%Y")

    def choose_trust_change(self):
        winsound.PlaySound("please_choose_trust_change", winsound.SND_FILENAME)
        #self.last_msg = "please_choose_trust_change"
        #self.msg_time = datetime.datetime.now().strftime("%I:%M:%S:%f %p %m-%d-%Y")

    def no_action(self):
        winsound.PlaySound("no_action_needed", winsound.SND_FILENAME)
        #self.last_msg = "no_action_needed"
        #self.msg_time = datetime.datetime.now().strftime("%I:%M:%S:%f %p %m-%d-%Y")

    def action_sound(self):
        winsound.PlaySound("take_control_now", winsound.SND_FILENAME)
        #self.last_msg = "take_control_now"
        #self.msg_time = datetime.datetime.now().strftime("%I:%M:%S:%f %p %m-%d-%Y")

    def obs_spotted(self):
        winsound.PlaySound("stopped_vehicle_ahead", winsound.SND_FILENAME)
        #self.last_msg = "stopped_vehicle_ahead"
        #self.msg_time = datetime.datetime.now().strftime("%I:%M:%S:%f %p %m-%d-%Y")

    def brake_sound(self):
        winsound.PlaySound("brake_tone", winsound.SND_FILENAME)
        #self.last_msg = "brake_tone"
        #self.msg_time = datetime.datetime.now().strftime("%I:%M:%S:%f %p %m-%d-%Y")

    def simulate(self):
        self.lock.acquire()
        while not self.course_finished():
            self.lock.release()
            print(self.client.getCarState().speed)
            if self.track_begin and self.client.getCarState().speed > self.ENABLE_V + 5:
                self.track_begin = False
                ena = threading.Thread(target=DriveSimulator.engage_auto, args=(self,))
                ena.start()

            self.lock.acquire()
            if not self.autoControl:
                if self.next_waypoint():
                    self.wp_idx += 1
            self.lock.release()


            self.calculate_ttc()
            self.play_feedback()

            time.sleep(0.1)
            self.lock.acquire()

    def start_simulation(self):
        sim = threading.Thread(target=DriveSimulator.simulate, args=(self,))
        sim.start()
        #uwp = threading.Thread(target=DriveSimulator.update_wp_man_mode, args=(self,))
        #uwp.start()
        cs = threading.Thread(target=DriveSimulator.control_switching, args=(self,))
        cs.daemon = True
        cs.start()



ds = DriveSimulator()
ds.start_simulation()


### Think about how to deal with different reliability conditions: sometimes certain obstacles shouldn't actually spawn

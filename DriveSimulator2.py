import PathFollower
import airsim
import pygame
import playsound
import threading
import math
import winsound
import time
import datetime
import csv
import pyttsx3
import monitoringRatioStream as mrs
import dataLogger as dl
from transforms3d import euler
from trustEstimator import trustEstimator
import sys
import collections

class DriveSimulator:

    START_Z = 6160.0
    bars_moved = False
    autoControl = False
    braking = False
    track_begin = True


    warning_played = False

    lock = threading.Lock()

    cur_trust = 0.0     # current trust score
    cur_trust_cov = 1.0 # current trust score covariance
    focus = 1.0         # focus variable (1 - gaze)
    performance = 0.0   # performance variable (points/sec, counting from last car passing time)
    usage = 0.0         # AUTO mode usage percentage

    end_sim = False
    last_mile = False

    cur_pilot_state = "calib"
    peblFilePath = '//ME-TILBURYLAB05/c$/Users/azevedo/Documents/pebl-exp.2.1/battery/vsearchForSlider/data.csv'

    speed_straight = 18.78  # 18.78 m/s = 42 mph
    speed_curvy = 15        #
    speed_dirt = 10


    def __init__(self, monitor_, track_type_, trust_controller_on_):

        self.track_type = track_type_
        if self.track_type == "regular":
            self.START_X = 452010.0
            self.START_Y = 352760.0
            self.road_condition = "straight"

        elif self.track_type == "reverse":
            self.START_X = 453190.0
            self.START_Y = 322260.0
            self.road_condition = "curvy"

        # set up controllers
        pygame.init()
        self.t = pygame.time.Clock()
        print("Number of Devices ", pygame.joystick.get_count())

        subjID = monitor_.subjID
        trialnum = monitor_.trialnum

        self.trust_controller_on = trust_controller_on_
        self.data_logger = dl.DataLogger(subjID, trialnum)


        self.d = pygame.joystick.Joystick(0) # initializes G-27 console OR Xbox controller
        self.d.init()

        # self.d2 = pygame.joystick.Joystick(0) # initializes G-27 console OR Xbox controller
        # self.d2.init()

        '''
        For some reason, after the rebuild, the Xbox controller is getting initialized earlier than the G-27 console.
        Therefore I needed to invert the pygame.joystick.Joystick(1) commands from 0 -> 1 to 1 -> 0;
        '''

        # assigns monitoringRatioStream object to the DriveSimulator
        self.monitor = monitor_

        # establish connection to AirSim
        self.client = airsim.CarClient()
        self.client.confirmConnection()
        self.client.enableApiControl(False)
        self.car_controls = airsim.CarControls()

        # reset vehicle to starting position if it isn't already there
        self.client.reset()

        if self.track_type == "regular":
            self.bar_names = ["Barrier_A-B_Straight", #0
                              "Barrier_C-D_Paved", #1
                              "Barrier_D-A_Paved", #2
                              "Barrier_A-B_Curvy", #3
                              "Barrier_C-D_Dirt", #4
                              "Barrier_D-A_Dirt", #5
                              "Barrier_B-C"] #6
        elif self.track_type == "reverse":
            self.bar_names = ["Barrier_A-B_Straight",
                              "Barrier_A-B_Curvy",
                              "Barrier_B-A_Curvy"]


        pose = self.client.simGetObjectPose("PhysXCar_camera_driver")
        pose.position.z_val -= 0.075
        pose.orientation.w_val = 0.66124517
        pose.orientation.x_val = 0.01638220
        pose.orientation.y_val = -0.01440479
        pose.orientation.z_val = 0.74985266
        self.client.simSetObjectPose("PhysXCar_camera_driver", pose, teleport=True)





        # set weather parameters
        self.client.simEnableWeather(True)
        self.client.simSetWeatherParameter(airsim.WeatherParameter.Fog, 0.5)

        # create path follower object and give it a path to follow
        if self.track_type == "regular":
            self.pf = PathFollower.PathFollower(self.START_X, self.START_Y, self.START_Z, self.speed_straight)

        if self.track_type == "reverse":
            self.pf = PathFollower.PathFollower(self.START_X, self.START_Y, self.START_Z, self.speed_curvy)

        #self.create_straight_path()
        if self.track_type == "regular":
            self.pf.input_path_csv("full_path.csv")
        elif self.track_type == "reverse":
            self.pf.input_path_csv("reverse_path.csv")
        self.wp_idx = 0

        self.obs = self.init_obs()
        self.obs_idx = 0

        if self.track_type == "regular":
            self.obs_close_radius_limit =     [90, 90, 90, 45, 45, 45, 45, 45, 45, 45, 0.01, 0.01, 1]
            self.obs_too_close_radius_limit = [40, 40, 40, 25, 25, 25, 25, 25, 25, 25, 15, 15, 1]
        elif self.track_type == "reverse":
            self.obs_close_radius_limit =     [45, 45, 45, 90, 90, 90, 45, 45, 45, 45, 32.5, 0.01, 1]
            self.obs_too_close_radius_limit = [25, 25, 25, 40, 40, 40, 25, 25, 25, 25, 25, 15, 1]

        # 1: True alarm; 0: False alarm; -1: Miss
        self.spawn = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        # get positions of barriers that need to move
        self.bar_pos = {}
        for barrier in self.bar_names:
            self.bar_pos[barrier] = self.client.simGetObjectPose(barrier)
            # print(self.bar_pos[barrier])
        self.bar_idx = 0

        self.set_barriers = False

        while not self.set_barriers:

            if self.track_type == "regular":
                self.lock.acquire()
                self.bar_pos["Barrier_A-B_Curvy"].position.z_val = 1000
                self.bar_pos["Barrier_C-D_Dirt"].position.z_val = 1000
                self.bar_pos["Barrier_D-A_Dirt"].position.z_val = 1000
                self.client.simSetObjectPose("Barrier_A-B_Curvy", self.bar_pos["Barrier_A-B_Curvy"])
                self.client.simSetObjectPose("Barrier_C-D_Dirt", self.bar_pos["Barrier_C-D_Dirt"])
                self.client.simSetObjectPose("Barrier_D-A_Dirt", self.bar_pos["Barrier_D-A_Dirt"])
                print("set barriers")
                self.lock.release()
            elif self.track_type == "reverse":
                self.lock.acquire()
                self.bar_pos["Barrier_A-B_Straight"].position.z_val = 1000
                self.client.simSetObjectPose("Barrier_A-B_Straight", self.bar_pos["Barrier_A-B_Straight"])
                print("set barriers")
                self.lock.release()

            if self.track_type == "regular":
                posAB = self.client.simGetObjectPose("Barrier_A-B_Curvy")
                posCD = self.client.simGetObjectPose("Barrier_C-D_Dirt")
                posDA = self.client.simGetObjectPose("Barrier_D-A_Dirt")
                if (posAB.position.z_val == 1000.0 and posCD.position.z_val == 1000.0 and posDA.position.z_val == 1000.0):
                    self.set_barriers = True
                else:
                    print("error setting barriers...")
            if self.track_type == "reverse":
                posAB = self.client.simGetObjectPose("Barrier_A-B_Straight")
                if (posAB.position.z_val == 1000.0):
                    self.set_barriers = True
                else:
                    print("error setting barriers...")


        self.last_event = time.time()
        self.monitor.set_last_event(self.last_event)

        self.minimumCarStateDict =  {
                                     'x' : 0.0,
                                     'y' : 0.0,
                                     'speed' : 0.0,
                                     'orientation' : 0.0
                                    }
        self.update_minimumCarState()

        self.afterHardBrake = False
        self.isHardBraking = False
        self.driver_state_trasitioned = False
        self.hardBrakeCounter = 0


        with open(self.peblFilePath, "w", newline='') as file:
            file.write(str(self.hardBrakeCounter))


        self.set_usage()


    def create_point(self, x, y):
        return (((x - self.START_X) / 100), ((y - self.START_Y) / 100))

    def init_obs(self):
        obs = []
        obs_file = ""
        if self.track_type == "regular":
            obs_file = "obstacles.csv"
        elif self.track_type == "reverse":
            obs_file = "reverse_path_obs.csv"
        with open(obs_file, "r") as csvfile:
            file = csv.reader(csvfile)
            for point in file:
                if len(point) == 2:
                    obs.append(self.create_point(float(point[0]), float(point[1])))
        return obs

    def create_straight_path(self):
        with open("path.csv", "w") as csvfile:
            file = csv.writer(csvfile)
            for i in range(-924000, 180000, 250):
                file.writerow([-175, i])
        self.wp_idx = 0

        self.obstacles = []
        self.warnings = []
        for i in range(-924000, 180000, 100000):
            self.obstacles.append([(-175 - self.START_X) / 100, (i - self.START_Y) / 100])
            self.warnings.append([(-175 - self.START_X) / 100, (i - self.START_Y) / 100 - 150])
        self.obs_idx = 0
        self.wrn_idx = 0
        print(self.obstacles)
        print(self.warnings)

    def filter(self, csvfile):
        with open(csvfile, "r") as path:
            with open("filtered_"+csvfile, "w+") as out:
                infile = csv.reader(path)
                outfile = csv.writer(out)
                pre_x = 0
                pre_y = 0
                for coord in infile:
                    if len(coord) == 2 and coord[0] != "nan" and coord[1] != "nan" and math.sqrt(((float(coord[0]) - pre_x) ** 2) + ((float(coord[1]) - pre_y) ** 2)) >= 100:
                        outfile.writerow([coord[0], coord[1]])
                        pre_x = float(coord[0])
                        pre_y = float(coord[1])
        return "filtered_"+csvfile

    def listen_user_break(self):
        while not self.end_sim:
            user_input = input()
            if user_input == "q":
                self.end_sim = True

    def control_switching(self): # This function checks the controller inputs periodically
        while not self.end_sim and pygame.event.get(pygame.QUIT) == []:
            xy = pygame.event.get(pygame.JOYAXISMOTION)

            if xy != []:
                xy_data = []
                for c in range(0, self.d.get_numaxes()):
                    xy_data += [str(round(self.d.get_axis(c), 1))]
                if self.autoControl == True and self.braking == False:
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
                    if self.autoControl == True and self.braking == False:
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
        r = 8.5
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def next_obs(self):
        x = self.minimumCarStateDict['x']
        y = self.minimumCarStateDict['y']

        h = self.obs[self.obs_idx][0]
        k = self.obs[self.obs_idx][1]

        r = 8.5
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def call_follow_path(self):
        while self.autoControl and not self.isHardBraking:
            self.lock.acquire()
            car_state = self.client.getCarState()
            car_controls = self.pf.follow_path(self.wp_idx, car_state)
            self.client.setCarControls(car_controls)
            self.lock.release()
            time.sleep(0.01)

    def obs_close(self):
        x = self.minimumCarStateDict['x']
        y = self.minimumCarStateDict['y']

        h = self.obs[self.obs_idx][0]
        k = self.obs[self.obs_idx][1]
        r = self.obs_close_radius_limit[self.obs_idx]
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    def obs_too_close(self):
        x = self.minimumCarStateDict['x']
        y = self.minimumCarStateDict['y']

        h = self.obs[self.obs_idx][0]
        k = self.obs[self.obs_idx][1]
        r = self.obs_too_close_radius_limit[self.obs_idx]
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


    def play_feedback(self):
        if self.autoControl:
            if self.obs_close() and not self.warning_played:
                if self.spawn[self.obs_idx] == 1:
                    wrn = threading.Thread(target=DriveSimulator.obs_spotted_message, args=(self,))
                    wrn.start()
                    self.warning_played = True

            if self.obs_too_close() and not self.isHardBraking:
                self.hard_brake()

    def calculate_pilot_state(self):

        trust_level = 0
        if self.cur_trust >= 25:
            trust_level = 1
        if self.cur_trust >= 75:
            trust_level = 2

        if self.road_condition == "straight" and trust_level == 0:
            calculated_driver_state = "under"
        if self.road_condition == "straight" and trust_level == 1:
            calculated_driver_state = "under"
        if self.road_condition == "straight" and trust_level == 2:
            calculated_driver_state = "calib"
        if self.road_condition == "curvy" and trust_level == 0:
            calculated_driver_state = "under"
        if self.road_condition == "curvy" and trust_level == 1:
            calculated_driver_state = "calib"
        if self.road_condition == "curvy" and trust_level == 2:
            calculated_driver_state = "over"
        if self.road_condition == "dirt" and trust_level == 0:
            calculated_driver_state = "calib"
        if self.road_condition == "dirt" and trust_level == 1:
            calculated_driver_state = "over"
        if self.road_condition == "dirt" and trust_level == 2:
            calculated_driver_state = "xover"
        return calculated_driver_state


    def get_usage(self): # gets the time percentage of AUTO usage

        time_now = time.time()
        self.time_before_car = self.time_before_car + (time_now - self.last_time)

        if self.autoControl:
            self.auto_time_before_car = self.auto_time_before_car + (time_now - self.last_time)

        try:
            usage = self.auto_time_before_car / self.time_before_car
        except:
            usage = 0.0

        self.last_time = time_now

        return usage

    def set_usage(self):
        self.last_time = self.last_event # sets last time instance as the passing time
        self.time_before_car = 0         # Period of time before obstacle car
        self.auto_time_before_car = 0    # Period of time in AUTO mode before obstacle car
        self.usage = 0                   # resets the usage



    def write_penalty_pebl(self):
        with open(self.peblFilePath, "w", newline='') as file:
            file.write(str(self.hardBrakeCounter))

    def simulate(self):
        while not self.end_sim:

            self.performance = self.monitor.get_perf()
            self.focus = self.monitor.get_focus()
            self.usage = self.get_usage()

            self.update_minimumCarState()

            if self.track_type == "regular":
                if self.wp_idx == len(self.pf.points) - 2:
                    self.end_sim = True
            elif self.track_type == "reverse":
                if self.wp_idx == len(self.pf.points) - 2:
                    self.end_sim = True


            # if it is hard braking, wait till speed goes close to zero to give back control to the driver
            if abs(self.minimumCarStateDict['speed']) < 0.01 and self.isHardBraking == True:
                self.lock.acquire()
                self.client.enableApiControl(False)
                self.lock.release()
                self.autoControl = False
                self.isHardBraking = False
                self.afterHardBrake = True

            # please_enable_autonomy_now message
            if not self.autoControl and self.track_begin and self.wp_idx == 2:
                self.track_begin = False
                ena = threading.Thread(target=DriveSimulator.engage_auto_message, args=(self,))
                ena.start()

            # keep track of waypoints
            if self.next_waypoint():
                if self.wp_idx == len(self.pf.points):
                    self.end_sim = True
                else:
                    self.wp_idx += 1
                # print(self.wp_idx)

            # keep track of obstacles and do all necessary transitions
            if self.next_obs():
                self.last_event = time.time()
                self.monitor.set_last_event(self.last_event)

                if self.obs_idx == 0:
                    self.cur_trust, self.cur_trust_cov = trustEstimator(self.cur_trust,
                                                                        self.cur_trust_cov,
                                                                        self.spawn[self.obs_idx] == 1,
                                                                        self.spawn[self.obs_idx] == 0,
                                                                        self.spawn[self.obs_idx] == -1,
                                                                        self.focus,
                                                                        self.performance,
                                                                        self.usage,
                                                                        True)
                    self.cur_trust = self.cur_trust[0][0][0]
                print(self.focus, " ", self.performance, " ", self.usage)

                self.cur_trust, self.cur_trust_cov = trustEstimator(self.cur_trust,
                                                                    self.cur_trust_cov,
                                                                    self.spawn[self.obs_idx] == 1,
                                                                    self.spawn[self.obs_idx] == 0,
                                                                    self.spawn[self.obs_idx] == -1,
                                                                    self.focus,
                                                                    self.performance,
                                                                    self.usage,
                                                                    False)
                self.cur_trust = self.cur_trust[0][0]
                trustResult = self.cur_trust

                print("Trust Estimate: " + str(trustResult))


                if self.afterHardBrake or self.isHardBraking:
                    self.hardBrakeCounter += 1
                    write_penalty = threading.Thread(target=DriveSimulator.write_penalty_pebl, args=(self,))
                    write_penalty.start()
                    self.afterHardBrake = False
                    self.isHardBraking = False

                self.monitor.pass_obstacle()

                self.warning_played = False
                self.obs_idx += 1

                if self.obs_idx >= 12:
                    self.last_mile = True

                if self.obs_idx > 12:
                    self.end_sim = True
                    print("Simulation Finished")

                if self.track_type == "regular" and self.obs_idx > 6 and not self.bars_moved:
                    print("move barriers")
                    self.lock.acquire()
                    # Set obstacles back into map
                    self.bar_pos["Barrier_A-B_Curvy"].position.z_val = 7
                    self.bar_pos["Barrier_C-D_Dirt"].position.z_val = 44.4
                    self.bar_pos["Barrier_D-A_Dirt"].position.z_val = 41.2
                    self.client.simSetObjectPose("Barrier_A-B_Curvy", self.bar_pos["Barrier_A-B_Curvy"])
                    self.client.simSetObjectPose("Barrier_C-D_Dirt", self.bar_pos["Barrier_C-D_Dirt"])
                    self.client.simSetObjectPose("Barrier_D-A_Dirt", self.bar_pos["Barrier_D-A_Dirt"])
                    self.lock.release()

                    self.lock.acquire()
                    # Move other obstacles out of view
                    self.bar_pos["Barrier_A-B_Straight"].position.z_val = 1000
                    self.bar_pos["Barrier_C-D_Paved"].position.z_val = 1000
                    self.bar_pos["Barrier_D-A_Paved"].position.z_val = 1000
                    self.client.simSetObjectPose("Barrier_A-B_Straight", self.bar_pos["Barrier_A-B_Straight"])
                    self.client.simSetObjectPose("Barrier_C-D_Paved", self.bar_pos["Barrier_C-D_Paved"])
                    self.client.simSetObjectPose("Barrier_D-A_Paved", self.bar_pos["Barrier_D-A_Paved"])
                    self.lock.release()



                    # if the barriers moved correctly...
                    if (self.client.simGetObjectPose("Barrier_A-B_Curvy").position.z_val == 7
                            and self.client.simGetObjectPose("Barrier_C-D_Dirt").position.z_val == 44.4
                            and self.client.simGetObjectPose("Barrier_D-A_Dirt").position.z_val == 41.2
                            and self.client.simGetObjectPose("Barrier_A-B_Straight").position.z_val == 1000
                            and self.client.simGetObjectPose("Barrier_C-D_Paved").position.z_val == 1000
                            and self.client.simGetObjectPose("Barrier_D-A_Paved").position.z_val == 1000):
                        self.bars_moved = True

                if self.track_type == "reverse" and self.obs_idx > 6 and not self.bars_moved:
                    print("move barriers")
                    self.lock.acquire()
                    # Set obstacles back into map
                    self.bar_pos["Barrier_A-B_Straight"].position.z_val = 7.2
                    self.client.simSetObjectPose("Barrier_A-B_Straight", self.bar_pos["Barrier_A-B_Straight"])
                    self.lock.release()

                    self.lock.acquire()
                    # Move other obstacles out of view
                    self.bar_pos["Barrier_A-B_Curvy"].position.z_val = 1000
                    self.bar_pos["Barrier_B-A_Curvy"].position.z_val = 1000
                    self.client.simSetObjectPose("Barrier_A-B_Curvy", self.bar_pos["Barrier_A-B_Curvy"])
                    self.client.simSetObjectPose("Barrier_B-A_Curvy", self.bar_pos["Barrier_B-A_Curvy"])
                    self.lock.release()
                    if (self.client.simGetObjectPose("Barrier_A-B_Straight").position.z_val == 7.2
                        and self.client.simGetObjectPose("Barrier_A-B_Curvy").position.z_val == 1000
                        and self.client.simGetObjectPose("Barrier_B-A_Curvy").position.z_val == 1000):
                        self.bars_moved = True

                self.set_usage()

                if self.track_type == "regular":
                    if self.obs_idx > 2 and self.road_condition == "straight":
                        self.road_condition = "curvy"
                        print("curvy")
                        self.pf.change_speed(self.speed_curvy)

                    if self.obs_idx > 9 and self.road_condition == "curvy":
                        self.road_condition = "dirt"
                        print("dirt road")
                        self.pf.change_speed(self.speed_dirt)

                    if self.obs_idx > 11 and self.road_condition == "dirt":
                        self.road_condition = "curvy"
                        pose_obstacleXX = self.client.simGetObjectPose("Sedan_SkelMesh8_23")
                        pose_obstacleXX.position.z_val = 1000
                        self.client.simSetObjectPose("Sedan_SkelMesh8_23", pose_obstacleXX)
                        print("curvy road. Gonna change the speed for the last time")
                        self.pf.change_speed(self.speed_curvy)

                elif self.track_type == "reverse":
                    if self.obs_idx == 3 and self.road_condition == "curvy":
                        self.road_condition = "straight"
                        print("changing to straight")
                        self.pf.change_speed(self.speed_straight)

                    if self.obs_idx == 6 and self.road_condition == "straight":
                        self.road_condition = "curvy"
                        print("changing to curvy")
                        self.pf.change_speed(self.speed_curvy)

                    if self.obs_idx == 11 and self.road_condition == "curvy":
                        self.road_condition = "dirt"
                        print("changing to dirt")
                        self.pf.change_speed(self.speed_dirt)

                    if self.obs_idx == 12 and self.road_condition == "dirt":
                        self.road_condition = "curvy"
                        print("changing to curvy")
                        self.pf.change_speed(self.speed_curvy)



                self.cur_pilot_state = self.calculate_pilot_state()
                print("######")
                self.driver_state_trasitioned = True

            self.play_feedback()
            time.sleep(0.01)
        self.lock.acquire()
        self.client.enableApiControl(False)
        self.client.simPause(True)
        self.lock.release()
        self.autoControl = False
        winsound.PlaySound('./audios/brake_tone', winsound.SND_FILENAME)

    def trust_controller(self):
        last_obstacle = self.obs_idx
        while not self.end_sim:
            current_obstacle = self.obs_idx
            # if current_obstacle != last_obstacle and not self.last_mile and self.driver_state_trasitioned:
            if not self.last_mile and self.driver_state_trasitioned:
                print("trust controller being called")
                if self.cur_pilot_state == "under":
                    sa = threading.Thread(target=DriveSimulator.SA_message, args=(self,))
                    sa.start()
                    print("pilot state: undertrusting")
                elif self.cur_pilot_state == "calib":
                    print("pilot state: calibrated")
                    pass
                elif self.cur_pilot_state == "over":
                    nudge = threading.Thread(target=DriveSimulator.nudge_message, args=(self,))
                    nudge.start()
                    print("pilot state: overtrusting")
                    # self.nudge_message()
                elif self.cur_pilot_state == "xover":
                    Xnudge = threading.Thread(target=DriveSimulator.Xnudge_message, args=(self,))
                    Xnudge.start()
                    print("pilot state: X-overtrusting")
                    # self.Xnudge_message()

            last_obstacle = current_obstacle
            self.driver_state_trasitioned = False
            time.sleep(0.01)

    def start_simulation(self):
        sim = threading.Thread(target=DriveSimulator.simulate, args=(self,))
        sim.start()

        cs = threading.Thread(target=DriveSimulator.control_switching, args=(self,))
        cs.start()

        if self.trust_controller_on:
            trust_control = threading.Thread(target=DriveSimulator.trust_controller, args=(self,))
            trust_control.start()

        data_logging = threading.Thread(target=DriveSimulator.log_data, args=(self,))
        data_logging.start()

        listen = threading.Thread(target=DriveSimulator.listen_user_break, args=(self,))
        listen.start()

    # Sound Functions
    def engage_auto_message(self):
        playsound.playsound('./audios/please_enable_autonomy_now.mp3', True)

    def obs_spotted_message(self):
        playsound.playsound('./audios/stopped_vehicle_ahead_take_control_now.mp3', True)

    def brake_sound(self):
        if not self.afterHardBrake:
            winsound.PlaySound('./audios/brake_tone', winsound.SND_FILENAME)

    def Hello_message(self):
        playsound.playsound('./audios/hello.mp3', True)

    def SA_message(self):
        time.sleep(5)
        playsound.playsound('./audios/SA_message.mp3', True)

    def nudge_message(self):
        time.sleep(5)
        playsound.playsound('./audios/nudge_message.mp3', True)

    def Xnudge_message(self):
        time.sleep(5)
        playsound.playsound('./audios/Xnudge_message.mp3', True)

    def log_data(self):
        while not self.end_sim:
            logVariablesDict  =  {
                                 'unixTime' : time.time(),
                                 'stdTime' : datetime.datetime.now().strftime("%I:%M:%S:%f %p %m-%d-%Y"),
                                 'AUTO' : self.autoControl,
                                 'Trust_Controller_ON' : self.trust_controller_on,
                                 'position_x' : self.minimumCarStateDict['x'],
                                 'position_y' : self.minimumCarStateDict['y'],
                                 'speed' : self.minimumCarStateDict['speed'],
                                 'orientation' : self.minimumCarStateDict['orientation'],
                                 'obstacleIndex' : self.obs_idx,
                                 'roadCondition' : self.road_condition,
                                 'pilotState' : self.cur_pilot_state,
                                 'pilotFocus' : self.focus,
                                 'pilotPerformance' : self.performance,
                                 'pilotUsage' : self.usage,
                                 'pilotTrustEstimate' : self.cur_trust
                                 }

            self.data_logger.write_line(logVariablesDict)
            time.sleep(0.1)

############ After class definition, start the threads



if len(sys.argv) < 3:
	print("Please provide subject ID and trial number, i.e., >> python sample_example_script.py 29 2")
	sys.exit()

subjID = int(sys.argv[1])
trialnum = int(sys.argv[2])

if (subjID % 4 == 1 or subjID % 4 == 2) and trialnum == 1:
    track_type = "regular"
if (subjID % 4 == 1 or subjID % 4 == 2) and trialnum == 2:
    track_type = "reverse"
if (subjID % 4 == 3 or subjID % 4 == 0) and trialnum == 1:
    track_type = "reverse"
if (subjID % 4 == 3 or subjID % 4 == 0) and trialnum == 2:
    track_type = "regular"

if (subjID % 4 == 1 or subjID % 4 == 0) and trialnum == 1:
    trust_controller_on = True
if (subjID % 4 == 1 or subjID % 4 == 0) and trialnum == 2:
    trust_controller_on = False
if (subjID % 4 == 2 or subjID % 4 == 3) and trialnum == 1:
    trust_controller_on = False
if (subjID % 4 == 2 or subjID % 4 == 3) and trialnum == 2:
    trust_controller_on = True


stream_obj = mrs.MonitoringRatioStream(subjID, trialnum)
mon = threading.Thread(target=stream_obj.stream)
mon.daemon = True
mon.start()
ds = DriveSimulator(stream_obj, track_type, trust_controller_on)
ds.Hello_message()
ds.start_simulation()

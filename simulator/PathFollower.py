import PidController as pc
import airsim
import time
import math
import csv
import threading
import matplotlib.pyplot as plt
from transforms3d import _gohlketransforms as gt


''''''''''''''' FUNCTIONS TO HELP WITH VECTOR MATH '''''''''''''''''''''
# vector subtraction, a - b
def sub(a, b):
    return {'x': a['x'] - b['x'], 'y': a['y'] - b['y'], 'z': a['z'] - b['z']}

# cross product
def cross(u, v):
    x = (u['y'] * v['z']) - (u['z'] * v['y'])
    y = (u['z'] * v['x']) - (u['x'] * v['z'])
    z = (u['x'] * v['y']) - (u['y'] * v['x'])
    return {'x': x, 'y': y, 'z': z}

# dot product
def dot(u, v):
    return (u['x'] * v['x']) + (u['y'] * v['y'])

# magnitude of vector u
def mag(u):
    return math.sqrt((u['x'] ** 2) + (u['y'] ** 2))

# angle between vector u and the x-axis
def angle(u):
    return math.atan2(u['y'], u['x'])

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


class PathFollower:

    # List of waypoints that makes up the path
    points = []

    # Get the AirSim object
    # x, y, and z are the starting coordinates of the vehicle in Unreal
    # speed is the desired speed of the vehicle in auto mode
    def __init__(self, x, y, z, speed):
        #self.client = client_
        self.START_X = x
        self.START_Y = y
        self.START_Z = z
        self.SPEED = speed

        self.steer = pc.PidController()
        self.steer.setPoint(0, 1.5, 0, 0.8)

        self.spd = pc.PidController()
        self.spd.setPoint(self.SPEED, 0.3, 0.0, 0.015)

    # returns the given coordinate as a dict, converted to AirSim coord system
    # the given (x, y) are the values from Unreal
    def create_waypoint(self, x, y):
        return {'x': (x - self.START_X) / 100, 'y': (y - self.START_Y) / 100, 'z': 0}

    # returns the position of the vehicle as a dict
    def position_point(self, car_state):
        pos = car_state.kinematics_estimated.position
        return {'x': pos.x_val, 'y': pos.y_val, 'z': pos.z_val}

    # returns the current orientation of the vehicle as a 3D vector (as a dict)
    def current_vector(self, car_state):
        quat = []
        quat.append(car_state.kinematics_estimated.orientation.w_val)
        quat.append(car_state.kinematics_estimated.orientation.x_val)
        quat.append(car_state.kinematics_estimated.orientation.y_val)
        quat.append(car_state.kinematics_estimated.orientation.z_val)
        M = gt.quaternion_matrix(quat)
        current = {'x': M[0][0], 'y': M[1][0], 'z': M[2][0]}
        return current

    # determines if the vehicle has "passed" the current waypoint
    # r is the radius of the circle around the waypoint
    # True --> set the new waypoint to the next in points[]
    # False --> continue targeting the current waypoint
    def next_waypoint(self, car_state):
        x = car_state.kinematics_estimated.position.x_val
        y = car_state.kinematics_estimated.position.y_val
        h = self.points[self.idx]['x']
        k = self.points[self.idx]['y']
        r = 3
        if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
            return True
        else:
            return False

    # constructs path from the given csv file
    # each row of infile is x, y
    def input_path_csv(self, infile):
        with open(infile, 'r') as csvfile:
            file = csv.reader(csvfile)
            for row in file:
                if len(row) == 2:
                    self.points.append(self.create_waypoint(float(row[0]), float(row[1])))

    def change_speed(self, speed):
        self.SPEED = speed
        self.spd.setPoint(self.SPEED, 0.3, 0.0, 0.015)

    # main function which causes the vehicle to follow the input path at the desired speed
    # start is the index of the path to start at
    def follow_path(self, start, car_state):
        #lock.acquire()
        car_controls = airsim.CarControls()

        self.idx = start


        #lock.release()
        #while True:
        #lock.acquire()
        #if not self.client.isApiControlEnabled():
        #         break
        #if self.next_waypoint(car_state):
        #    if self.idx == len(self.points) - 1:
        #        return car_controls
        #    self.idx += 1
        #print(self.idx, ": ", self.points[self.idx])
        path = sub(self.points[self.idx], self.position_point(car_state))
        beta = angle(path)
        alpha = angle(self.current_vector(car_state))
        theta = alpha - beta
        if theta > math.pi:
            theta = (theta % math.pi) - math.pi
        if theta < (-1 * math.pi):
            theta = math.pi - ((-1 * theta) % math.pi)
        #print(theta)
        car_controls.steering = self.steer.control(theta)
        spd_out = self.spd.control(car_state.speed)

        # if spd_out < 0: spd_out = 0
        # if spd_out >= 1: spd_out = 1

        car_controls.is_manual_gear = True
        car_controls.manual_gear = 2

        car_controls.throttle = spd_out

        if spd_out < 0:
            car_controls.brake = spd_out
            car_controls.throttle = 0

        return car_controls
        #self.client.setCarControls(car_controls)
        #lock.release()
        #time.sleep(0.1)

        #car_controls.throttle = 0
        #car_controls.steering = 0
        #car_controls.handbrake = True
        #self.client.setCarControls(car_controls)






















'''
def create_waypoint_nocon(x, y):
    return {'x': x, 'y': y, 'z': 0}





def print_accel():
    print("x accel: " + str(client.getCarState().kinematics_estimated.linear_acceleration.x_val))
    print("y accel: " + str(client.getCarState().kinematics_estimated.linear_acceleration.y_val))
    print("z accel: " + str(client.getCarState().kinematics_estimated.linear_acceleration.z_val))
    print("")

def print_velocity():
    print("x velocity: " + str(client.getCarState().kinematics_estimated.linear_velocity.x_val))
    print("y velocity: " + str(client.getCarState().kinematics_estimated.linear_velocity.y_val))
    print("z velocity: " + str(client.getCarState().kinematics_estimated.linear_velocity.z_val))
    print("")

def print_orientation():
    print("w orientation: " + str(client.getCarState().kinematics_estimated.orientation.w_val))
    print("x orientation: " + str(client.getCarState().kinematics_estimated.orientation.x_val))
    print("y orientation: " + str(client.getCarState().kinematics_estimated.orientation.y_val))
    print("z orientation: " + str(client.getCarState().kinematics_estimated.orientation.z_val))
    print("")

def print_position():
    print("x position: " + str(client.getCarState().kinematics_estimated.position.x_val))
    print("y position: " + str(client.getCarState().kinematics_estimated.position.y_val))
    print("z position: " + str(client.getCarState().kinematics_estimated.position.z_val))
    print("")


def set_speed(pid, target, k_p, k_i, k_d, duration, t):
    pid.setPoint(target, k_p, k_i, k_d)
    for i in range (0, duration):
        output = pid.control(client.getCarState().speed)
        if output > 1: output = 1
        if output < 0: output = 0
        car_controls.throttle = output
        #print(str(car_controls.throttle) + ", " + str(client.getCarState().speed) + "\n")
        time_x.append(t)
        speed_y.append(client.getCarState().speed)
        target_y.append(target)
        throttle_y.append(output)
        client.setCarControls(car_controls)
        t += 0.1
        time.sleep(0.1)
    return t



def create_figure_eight():
    points = []
    a = 40
    list_x = []
    list_y = []
    for x in range(-40, 0, 20):
        y = math.sqrt(x**2 - (x**4 / a**2))
        points.append(create_waypoint_nocon(x, y))
        list_x.append(x)
        list_y.append(y)
    for x in range(0, 40, 20):
        y = -1 * math.sqrt(x**2 - (x**4 / a**2))
        points.append(create_waypoint_nocon(x, y))
        list_x.append(x)
        list_y.append(y)
    for x in range(40, 0, -20):
        y = math.sqrt(x**2 - (x**4 / a**2))
        points.append(create_waypoint_nocon(x, y))
        list_x.append(x)
        list_y.append(y)
    for x in range(0, -40, -20):
        y = -1 * math.sqrt(x**2 - (x**4 / a**2))
        points.append(create_waypoint_nocon(x, y))
        list_x.append(x)
        list_y.append(y)
    #plt.plot(list_x, list_y, label="fig eight")
    #plt.show()
    return points



client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(True)
car_controls = airsim.CarControls()

client.reset()

#car_controls.throttle = 0.7
#client.setCarControls(car_controls)

current = current_vector()


x = {'x': 1, 'y': 0, 'z': 0}

points = create_figure_eight()
#print(points)
'''
'''
#BIG RECTANGLE THINGS
points.append(create_waypoint(8000.0, 16000.0))
points.append(create_waypoint(8000.0, 22000.0))
points.append(create_waypoint(11634.0, 30000.0))
points.append(create_waypoint(8000.0, 22000.0))
points.append(create_waypoint(11634.0, 30000.0))
points.append(create_waypoint(8000.0, 22000.0))
points.append(create_waypoint(11634.0, 30000.0))
points.append(create_waypoint(8000.0, 22000.0))
points.append(create_waypoint(17164.0, 32108.0))
'''
'''
#FIGURE EIGHT
points.append(create_waypoint(60000.0, 40000.0))
points.append(create_waypoint(58000.0, 42000.0))
points.append(create_waypoint(60000.0, 44000.0))
points.append(create_waypoint(62000.0, 42000.0))
points.append(create_waypoint(60000.0, 40000.0))
points.append(create_waypoint(58000.0, 38000.0))
points.append(create_waypoint(60000.0, 36000.0))
points.append(create_waypoint(62000.0, 38000.0))
points.append(create_waypoint(60000.0, 40000.0))
'''


'''
time_x = []
target_y = []
alpha_y = []
steering_y = []
t = 0


car_controls.handbrake = True
car_controls.throttle = 0
client.setCarControls(car_controls)
client.enableApiControl(False)

plt.plot(time_x, alpha_y, label="vehicle angle")
plt.plot(time_x, target_y, label="target angle")
plt.plot(time_x, steering_y, label="steering")
plt.xlabel("Time (s)")
plt.ylabel("Angle from x (rad)")
#plt.title("k_p: " + str(k_p) + ", k_i: " + str(k_i) + ", k_d: " + str(k_d))
#plt.savefig("PID Graphs\\pidgraph_" + str(k_p) + "_" + str(k_i) + "_" + str(k_d) + "_" + str(t) + ".png")
plt.show()
'''
'''
time_x = []
speed_y = []
target_y = []
throttle_y = []

k_p = 0.8
k_i = 0.1
k_d = 0.05
# 0.5, 0.15, 0.025

t = 0

pid = pc.PidController()

target = 10
t = set_speed(pid, target, k_p, k_i, k_d, 250, t)

target = 20
t = set_speed(pid, target, k_p, k_i, k_d, 250, t)

target = 30
t = set_speed(pid, target, k_p, k_i, k_d, 250, t)


client.enableApiControl(False)


plt.plot(time_x, speed_y, label="vehicle speed")
plt.plot(time_x, target_y, label="target speed")
plt.plot(time_x, throttle_y, label="throttle")
plt.xlabel("Time (s)")
plt.ylabel("Speed (m/s)")
plt.title("k_p: " + str(k_p) + ", k_i: " + str(k_i) + ", k_d: " + str(k_d))
plt.savefig("PID Graphs\\pidgraph_" + str(k_p) + "_" + str(k_i) + "_" + str(k_d) + "_" + str(t) + ".png")
plt.show()
'''

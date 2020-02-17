import PathFollower as pf
import airsim
import threading
import time
import csv

idx = 0

def next_waypoint():
    global idx
    x = client.getCarState().kinematics_estimated.position.x_val
    y = client.getCarState().kinematics_estimated.position.y_val
    h = follower.points[idx]['x']
    k = follower.points[idx]['y']
    r = 6
    if r ** 2 >= ((x - h) ** 2) + ((y - k) ** 2):
        return True
    else:
        return False

outfile = "path.csv"

with open(outfile, 'w') as csvfile:
    file = csv.writer(csvfile)
    for i in range(-924000, 180000, 1000):
        file.writerow([-175, i])

def update_wp_man_mode():
    global idx
    while not client.isApiControlEnabled():
        if next_waypoint():
            idx += 1
        time.sleep(0.1)

def listen():
    global idx
    cmd = input()
    while not cmd == 'q':
        if cmd == 'm' and client.isApiControlEnabled():
            client.enableApiControl(False)
            idx = follower.idx
            #print idx
            update_idx = threading.Thread(target=update_wp_man_mode)
            update_idx.daemon = True
            update_idx.start()
        if cmd == 'a':
            if not client.isApiControlEnabled():
                client.enableApiControl(True)
                flw = threading.Thread(target=follower.follow_path, args=[idx])
                flw.start()
        cmd = input()
        time.sleep(0.1)
    client.enableApiControl(False)

client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(True)
car_controls = airsim.CarControls()

client.reset()

follower = pf.PathFollower(client, -175.0, -925000.0, 50, 30)
follower.input_path_csv("path.csv")
flw = threading.Thread(target=follower.follow_path, args=[idx])
flw.start()

lst = threading.Thread(target=listen)
lst.start()

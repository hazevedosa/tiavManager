import airsim
import csv
import threading
import time

stop = False

def listen():
    global stop
    command = input()
    if command == 'q':
        stop = True

client = airsim.CarClient()
client.confirmConnection()
client.enableApiControl(False)
car_controls = airsim.CarControls()

client.reset()

start_x = 439959.03125
start_y = 352417.125
filename = "append_to_reverse_path.csv"

outfile = open(filename, "w+")
of = csv.writer(outfile)

lst = threading.Thread(target=listen)
lst.daemon = True
lst.start()

while not stop:
    x = client.simGetObjectPose("PhysXCar").position.x_val
    y = client.simGetObjectPose("PhysXCar").position.y_val
    x = (x * 100) + start_x
    y = (y * 100) + start_y
    of.writerow([x, y])
    print(x, " ", y)
    time.sleep(0.5)

outfile.close()

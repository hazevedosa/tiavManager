import zmq
from msgpack import loads
import subprocess as sp
from platform import system
import time
import signal
import csv

from trustEstimator import trustEstimator

class MonitoringRatioStream:

    surface_names = ["PEBL Screen", "Right Monitor", "Center Monitor", "Left Monitor"]
    initialRow = 0
    obs_passed = False

    def __init__(self, subjID_, trialnum_):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.performance = 0.0
        self.focus = 1.0

        self.subjID = subjID_
        self.trialnum = trialnum_

        self.filePath = "//ME-TILBURYLAB05/c$/Users/azevedo/Documents/pebl-exp.2.1/battery/vsearchForSlider/data/sub" + str(self.subjID) + "_trial" + str(self.trialnum) + "/vsearch-sub" + str(self.subjID) + "_trial" + str(self.trialnum) + ".csv"

        # self.filePath = "//ME-TILBURYLAB05/c$/Users/azevedo/Documents/pebl-exp.2.1/battery/vsearchForSlider/data/sub1_trial1/vsearch-sub1_trial1.csv"
        with open(self.filePath, "w", newline='') as file:
            logger = csv.writer(file)
            logger.writerow([
                            'sub',
                            'trial',
                            'time',
                            'numtargs',
                            'size',
                            'targchar',
                            'targcol',
                            'stim',
                            'resp',
                            'corr',
                            'rt1',
                            'rt2',
                            'score'
                            ])


    def read_numbers(self):
        data = []
        with open(self.filePath) as csvfile:
            readCSV = csv.reader(csvfile, delimiter = ',')
            # row_index = 0
            for row in readCSV:
                if row:
                    # row_index += 1
                    columns = [row[0], row[1], row[2], row[3], row[4], row[5],
                               row[6], row[7], row[8], row[9], row[10], row[11], row[12]]
                    data.append(columns)


        if (data[-1][-1] == 'score'):
            return 0
        elif data[self.initialRow][2] == data[-1][2]:
            return 0
        elif self.initialRow == 0:
            return float(data[-1][-1])
        else:
            return float(data[-1][-1]) - float(data[self.initialRow][-1])

    def set_last_event(self, event_time):
        self.last_event = event_time

    def pass_obstacle(self):
        self.obs_passed = True

    def get_focus(self):
        return self.focus

    def get_perf(self):
        return self.performance

    def read_new_initialRow(self):
        # filePath = "//ME-TILBURYLAB05/c$/Users/azevedo/Documents/pebl-exp.2.1/battery/vsearchForSlider/data/subjTest/vsearch-subjTest.csv"
        filePath = "//ME-TILBURYLAB05/c$/Users/azevedo/Documents/pebl-exp.2.1/battery/vsearchForSlider/data/sub" + str(self.subjID) + "_trial" + str(self.trialnum) + "/vsearch-sub" + str(self.subjID) + "_trial" + str(self.trialnum) + ".csv"
        data = []
        with open(filePath) as csvfile:
            readCSV = csv.reader(csvfile, delimiter = ',')
            for row in readCSV:
                if row:
                    columns = [row[0], row[1], row[2], row[3], row[4], row[5],
                               row[6], row[7], row[8], row[9], row[10], row[11], row[12]]
                    data.append(columns)
        if (data[-1][-1] == 'score'):
            return 0
        else:
            return float(data[-1][1])


    def stream(self):
        context = zmq.Context()
        # open a req port to talk to pupil
        addr = "127.0.0.1"  # remote ip or localhost
        req_port = "50020"  # same as in the pupil remote gui --- gotta check
        req = context.socket(zmq.REQ)
        req.connect("tcp://{}:{}".format(addr, req_port))
        # ask for the sub port
        req.send_string("SUB_PORT")
        sub_port = req.recv_string()

        # open a sub port to listen to pupil
        sub = context.socket(zmq.SUB)
        sub.connect("tcp://{}:{}".format(addr, sub_port))
        sub.setsockopt_string(zmq.SUBSCRIBE, f"surfaces.{self.surface_names[0]}")
        sub.setsockopt_string(zmq.SUBSCRIBE, f"surfaces.{self.surface_names[1]}")
        sub.setsockopt_string(zmq.SUBSCRIBE, f"surfaces.{self.surface_names[2]}")
        sub.setsockopt_string(zmq.SUBSCRIBE, f"surfaces.{self.surface_names[3]}")

        sub.RCVTIMEO = 25

        initialTime = time.time()
        t_0 = initialTime

        on_off_flag = True
        on_total_time = 0

        m_prev = 0
        self.performance = 0
        while True:
            try:
                topic, msg = sub.recv_multipart()
                gaze_position = loads(msg, raw = False)

                # print(gaze_position)

                # if (gaze_position["name"] == surface_names[1]) or (gaze_position["name"] == surface_names[2]) or (gaze_position["name"] == surface_names[3]):
                if (gaze_position["name"] == self.surface_names[0]):
                    gaze_on_screen = gaze_position["gaze_on_surfaces"]
                    if len(gaze_on_screen) > 0:
                        if gaze_on_screen[0]['on_surf'] == True:
                            # print("I am here in on")
                            on_off_flag = True
                        else:
                            # print("I am here in off 1")
                            on_off_flag = False
                else:
                    # print("I am here in off 3")
                    on_off_flag = False
            except:
                # print("I am reaching the timeout")
                pass

            t_1 = time.time()
            total_time = t_1 - initialTime

            if on_off_flag == True:
                on_total_time += t_1 - t_0
            else:
                pass

            t_0 = t_1

            monitoringRatio = on_total_time / total_time
            self.focus = monitoringRatio

            m = self.read_numbers()
            if m > m_prev:
                n = m / (time.time() - self.last_event)
                self.performance = n

            m_prev = m

            if self.obs_passed == True:
                print("points scored in the last period: " + str(m))
                self.initialRow = int(self.read_new_initialRow())
                initialTime = time.time()
                t_0 = initialTime
                on_total_time = 0.0
                self.performance = 0.0
                self.obs_passed = False
            time.sleep(0.01)

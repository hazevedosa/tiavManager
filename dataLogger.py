import csv

class DataLogger:

    def __init__(self, subjID_, trialnum_):
        self.filepathname = "./loggingTests/" + "drivingSub-" + str(subjID_) + "-trial-" + str(trialnum_) + ".csv"
        # write the header
        with open(self.filepathname, "w", newline='') as file:
            logger = csv.writer(file)
            logger.writerow([
                            'unixTime',
                            'stdTime',
                            'AUTO',
                            'Trust_Controller_ON',
                            'position_x',
                            'position_y',
                            'speed',
                            'orientation',
                            'obstacleIndex',
                            'roadCondition',
                            'pilotState',
                            'pilotFocus',
                            'pilotPerformance',
                            'pilotUsage',
                            'pilotTrustEstimate'
                            ])


    def write_line(self, logVariablesDict):
        with open(self.filepathname, "a", newline='') as file:
            logger = csv.writer(file)
            logger.writerow([
                            logVariablesDict['unixTime'],
                            logVariablesDict['stdTime'],
                            logVariablesDict['AUTO'],
                            logVariablesDict['Trust_Controller_ON'],
                            logVariablesDict['position_x'],
                            logVariablesDict['position_y'],
                            logVariablesDict['speed'],
                            logVariablesDict['orientation'],
                            logVariablesDict['obstacleIndex'],
                            logVariablesDict['roadCondition'],
                            logVariablesDict['pilotState'],
                            logVariablesDict['pilotFocus'],
                            logVariablesDict['pilotPerformance'],
                            logVariablesDict['pilotUsage'],
                            logVariablesDict['pilotTrustEstimate']
                            ])

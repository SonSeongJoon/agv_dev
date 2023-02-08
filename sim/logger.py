import json
import configparser
import time
import csv
from datetime import datetime
import os

class Logger:
    def __init__(self, configFile, fixedPickUpPoint ,fixedDropOffPoint):
        config = configparser.ConfigParser()
        config.read(configFile)
        self.txtfilename = config.get('LOG','txtfilename')
        self.csvfilename = config.get('LOG','csvfilename')
        height = config.getint('MAP','height')
        width = config.getint('MAP','width')
        queueMargin = config.getint('MAP','queueMargin')
        gridSize = config.getfloat('MAP','gridSize')
        self.simulation = {}
        
        data = {}
        data['setup'] = {
            "width": width,
            "height": height,
            "gridSize": gridSize,
            "queueMargin": queueMargin,
            "fixedPickUpPoint": fixedPickUpPoint,
            "fixedDropOffPoint": fixedDropOffPoint
        }
        now = datetime.now().strftime("%d-%m_%H%M")
        # folderPath = f'sim/{now}'
        folderPath = f'sim/turning'  # DEBUG: for turning
        isExist = os.path.exists(folderPath)
        if not isExist:
            os.makedirs(folderPath)
        
        self.txtPath = f'{folderPath}/{self.txtfilename}'
        self.csvPath = f'{folderPath}/{self.csvfilename}'
        # self.txtPath = self.txtfilename
        # self.csvPath = self.csvfilename
        
        with open(self.txtPath,'w') as f:
            f.truncate()
            f.write(str(data)+'\n')
        
        header = ['id', 'agv', 'initTime', 'assignTime', 'pickupTime', 'comepleteTime']
        
        with open(self.csvPath,'w',newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
        
    def log(self, data):
        with open(self.txtPath, 'a') as f:
            f.write(str(data)+'\n')

    def logTask(self, data):
        if data:
            with open(self.csvPath,'a', newline='') as f:
                writer = csv.writer(f)
                for row in data:
                    writer.writerow(list(row.values()))
import json
import os
from mapper import Mapper
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.artist import Artist
import configparser
from tqdm import tqdm


configFile = 'config.ini'

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(configFile)
    filename = config['REPLAY']['filename']
    agvSize = config.getfloat('AGV','agvSize')
    playbackSpeed = config.getfloat('REPLAY','playbackSpeed')

    data = []

    with open(filename, 'r') as f:
        num_lines = sum(1 for line in f)
        start = 0
        # start = num_lines-100  #DEBUG
        f.seek(0)
        setup = eval(f.readline())['setup']
        for i, line in enumerate(tqdm(f, total=num_lines)):
            if i > start:
                line = eval(line)
                data.append(line)
    
    coordX = []
    coordY = []
    spd = []
    for i, line in enumerate(data):
        coordX.append(line['agv'][0]['currentCoord'][0])
        coordY.append(line['agv'][0]['currentCoord'][1])
        spd.append(line['agv'][0]['speed'])
    
    print(coordY)
    plt.plot(coordY, 'o')
    plt.show()
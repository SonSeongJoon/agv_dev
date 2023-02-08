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
    
    if config.has_option('TASK', 'fixedPickUpPoint'):
        fixedPickUpPoint = json.loads(config['TASK']['fixedPickUpPoint'])
    else:
        fixedPickUpPoint = None
    if config.has_option('TASK', 'fixedDropOffPoint'):
        fixedDropOffPoint = json.loads(config['TASK']['fixedDropOffPoint'])
    else:
        fixedDropOffPoint = None
    
    if not os.path.exists(f'./{filename}'):
        print("File does not exist: {}".format(filename))
        exit()
    
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
    
    height = setup['height']
    width = setup['width']
    gridSize = setup['gridSize']
    queueMargin = setup['queueMargin']
    fixedPickUpPoint = setup['fixedPickUpPoint']
    fixedDropOffPoint = setup['fixedDropOffPoint']
    
    fig, ax = plt.subplots()
    mapper = Mapper(height=height, width=width, length=gridSize)
    mapper.initRectagnleMap(height=height, width=width, length=gridSize)
    # mapper.initCircleDirectedRectagnleMap(height=height, width=width, length=gridSize, margin=queueMargin)
    mapper.drawGrid()
    
    ax.set_xlim((-gridSize, width*gridSize))
    ax.set_ylim((-gridSize, height*gridSize))
    ax.set_aspect('equal', anchor='C')
    plt.tight_layout()
    
    agvNum = len(data[0]['agv'])
    artists=[]
    checkedLoc = []
    
    if fixedPickUpPoint:
        for point in fixedPickUpPoint:
            x, y = mapper.pointConvertCoord(point)
            plt.scatter(x,y, s=30,c='g',marker='v')
        
    if fixedDropOffPoint:
        for point in fixedDropOffPoint:
            x, y = mapper.pointConvertCoord(point)
            plt.scatter(x,y, s=30,c='b',marker='^')
    
    plt.pause(0.5)
    
    
    for i, line in enumerate(data):
        if i == 1:
            input("Press any key to continue")
        
        if i%playbackSpeed != 0 and i != len(data)-1:
            continue
        
        # print('time: ', round(line['time'], 2))
        
        for id in range(agvNum):
            
            x,y = line['agv'][id]['currentCoord']
            
            if line['agv'][id]['status'] == 1:
                agv = patches.Rectangle(xy=(x-agvSize/2,y-agvSize/2), width=agvSize, height=agvSize, fill=True, ec='k',color='tab:blue', label=str(id),zorder=4)
            elif line['agv'][id]['status'] in [2,3,4,5]:
                agv = patches.Rectangle(xy=(x-agvSize/2,y-agvSize/2), width=agvSize, height=agvSize, fill=True, ec='k',color='tab:orange', label=str(id),zorder=4)
            elif line['agv'][id]['status'] == 6:
                agv = patches.Rectangle(xy=(x-agvSize/2,y-agvSize/2), width=agvSize, height=agvSize, fill=True, ec='k',color='y', label=str(id),zorder=4)
            elif line['agv'][id]['status'] == 99:
                agv = patches.Rectangle(xy=(x-agvSize/2,y-agvSize/2), width=agvSize, height=agvSize, fill=True, ec='k',color='r', label=str(id),zorder=4)

            ax.add_patch(agv)
            artists.append(agv)
            artists.append(ax.annotate(id, (x, y), color='b', weight='bold', fontsize='medium', ha='center', va='center', zorder=4))
            
        if line['crashedAGV']:
            for j, loc in enumerate(line['crashedLocation']):
                if loc not in checkedLoc:
                    x, y = loc
                    crashedArea = patches.Circle(xy=(x,y), radius=0.3, fill=True, ec='k',color='yellow',zorder=0, lw=0)
                    ax.add_patch(crashedArea)
                    plt.scatter(x,y, s=300,c='r',marker='x')
                    ax.annotate(j+1, (x, y), color='k', weight='bold', fontsize='small', ha='center', va='center', zorder=4)
                    checkedLoc.append(loc)
        
        
        # print("Time: {} AGV {} coord ({},{})".format(round(line['time']), id, x, y))
        
        plt.pause(0.01)
        
        if i != len(data)-1:
            for art in artists:
                Artist.remove(art)
            artists.clear()
        
        
    
    crashedAGV = line['crashedAGV']
        
        # size = fig.get_size_inches()*fig.dpi
        # print(size)
        # input()
        
    print("---Statistics---")
    print("Crashed times: ", len(crashedAGV))
    print("Crashed AGV: ", crashedAGV)
    
    input("Press any key to close")
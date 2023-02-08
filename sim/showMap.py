from mapper import Mapper
import configparser
import json
import math
import os

configFile = 'config.ini'

def run():
    os.system('cls')
    
    config = configparser.ConfigParser()
    config.read(configFile)
    height = config.getint('MAP','height')
    width = config.getint('MAP','width')
    gridSize = config.getfloat('MAP','gridSize')
    fixedPickUpPoint = json.loads(config['TASK']['fixedPickUpPoint'])
    fixedDropOffPoint = json.loads(config['TASK']['fixedDropOffPoint'])
    idlePoint = json.loads(config['TASK']['idlePoint'])
    
    totalPoints = height*width
    if not fixedPickUpPoint:
        fixedPickUpPoint = list(range(totalPoints - height, totalPoints -1))
    if not fixedDropOffPoint:
        fixedDropOffPoint = list(range(math.ceil(height*.25), math.floor(height*.75)))
    if not idlePoint:
        idlePoint = [height * x for x in range(1, width-4)]
    if len(idlePoint) > (width-4):
        raise ValueError('More idle points than the map width')
    
    print('Map Data')
    print(f'Map Size: {height} x {width} total points: {height*width}')
    print('fixedPickUpPoint', fixedPickUpPoint)
    print('fixedDropOffPoint', fixedDropOffPoint)
    print('idlePoint',idlePoint)
    
    
    mapper = Mapper()
    mapper.initRectagnleMap(height, width, gridSize)
    ## for showing map
    mapper.draw(show=True)

if __name__ == '__main__':
    run()
import time
from fms import FMS
from mapper import Mapper
from taskGenerator import TaskGenerator
from logger import Logger
import random
import configparser
import json
from memory_profiler import profile
import os
from orderProcessor import OrderProcessor
from tqdm import tqdm
from datetime import datetime, timedelta

configFile = 'config.ini'

# @profile
def run():
    # os.system('cls')
    # os.system('clear')
    random.seed(5)
    
    config = configparser.ConfigParser()
    config.read(configFile)
    numberOfAGV = config.getint('AGV','numberOfAGV')
    agvSPD = config.getfloat('AGV','agvSPD')
    agvACL = config.getfloat('AGV','agvACL')
    agvRotateSPD = config.getfloat('AGV','agvRotateSPD')
    height = config.getint('MAP','height')
    width = config.getint('MAP','width')
    gridSize = config.getfloat('MAP','gridSize')
    queueMargin = config.getfloat('MAP','queueMargin')
    sampleTime = config.getfloat('MAP','sampleTime')
    numberOfTasks = config.getint('SIM','NUMBEROFTASKS')
    csvPath = config.get('SIM','csvPath')
    fixedPickUpPoint = json.loads(config['TASK']['fixedPickUpPoint'])
    fixedDropOffPoint = json.loads(config['TASK']['fixedDropOffPoint'])
    idlePoint = json.loads(config['TASK']['idlePoint'])
    orderPickUpPoint=None
    orderDropOffPoint=None
    manualPoint = []

    mapper = Mapper(height=height, width=width, length=gridSize)
    
    if numberOfTasks == -3:
        orderProcessor = OrderProcessor(csvFile=csvPath)
        
        orderProcessor.filterManualProcess()
        orderPickUpPoint = orderProcessor.getPickupPoint()
        orderDropOffPoint = orderProcessor.getDropoffPoint()
        orderData = orderProcessor.getOrderData()
        
        fixedPickUpPoint = mapper.convertPickupPoint(orderPickUpPoint=orderPickUpPoint)
        fixedDropOffPoint, manualPoint = mapper.convertDropoffPoint(orderDropOffPoint=orderDropOffPoint.copy())
    
    totalPoints = height*width
    if not fixedPickUpPoint:
        fixedPickUpPoint = list(range(totalPoints - width, totalPoints,2))
    if not fixedDropOffPoint:
        fixedDropOffPoint = list(range(1, width,2))
    
    print('Map Data')
    print('fixedPickUpPoint')
    print((fixedPickUpPoint))
    print('fixedDropOffPoint')
    print((fixedDropOffPoint))
    print('idlePoint')
    print(idlePoint)
    if numberOfTasks == -3: 
        print('orderPickUpPoint')
        print((orderPickUpPoint))
        print('orderDropOffPoint')
        print((orderDropOffPoint))
    # input()
    
    mapper.initCircleDirectedRectagnleMap(height=height, width=width, length=gridSize, margin=queueMargin)
    ## for showing map
    # mapper.draw(show=True)
    # exit()
    
    # input("press to start")
    logger = Logger(configFile=configFile, fixedPickUpPoint=fixedPickUpPoint, fixedDropOffPoint=fixedDropOffPoint)
    fms = FMS(mapper=mapper, sampleTime=sampleTime, fixedPickUpPoint=fixedPickUpPoint, fixedDropOffPoint=fixedDropOffPoint, manualPoint=manualPoint)
    taskgen = TaskGenerator(mapPoints=mapper.getNumberofPoints()-1, fixedPickUpPoint=fixedPickUpPoint, fixedDropOffPoint=fixedDropOffPoint, orderPickUpPoint=orderPickUpPoint, orderDropOffPoint=orderDropOffPoint)
    
    if numberOfAGV > len(fixedDropOffPoint):
        initPoint=mapper.initHorizontal(numberOfAGV)
    else:
        initPoint = fixedDropOffPoint[:numberOfAGV]
        initPoint = list(int(x+(height/2)*width - 1) for x in initPoint)
        
    # initPoint=mapper.generateRandomPoints(numberOfAGV)
    print('initPoint', initPoint)
    fms.addAGV(numberOfAGV, agvSPD, agvACL ,agvRotateSPD,initPoint)
    #* hardcoded mapepr into AGV, should have a better design of this 

    if numberOfTasks >= -2: 
        if numberOfTasks == -1:
            numberOfTasks=numberOfAGV  
        elif numberOfTasks == -2: 
            numberOfTasks=50
        
        for t in range(int(numberOfTasks)):
            # task = taskgen.generateRandomTask(initTime=t)
            task = taskgen.generateRandomTask(initTime=t/2, duplicate=False)

            # task = taskgen.generateSimpleTask(start=fixedPickUpPoint[10], dest=fixedDropOffPoint[-2], initTime=t)
            # task = taskgen.generateSimpleTask(start=95, dest=4, initTime=0)
            # task.info()
            fms.addTaskToScheduler(task)
    elif numberOfTasks == -3: 
        taskAmount = len(orderData)
        # taskAmount = 2000  #DEBUG
        for i in tqdm(range(taskAmount)):
            # if i > 11100: #DEBUG
            task = taskgen.generateTask(orderPickup=orderData.T[i]['pickup'], orderDropoff=orderData.T[i]['dropoff'], initTime=orderData.T[i]['time'])
            # task = taskgen.generateTask(orderPickup=80, orderDropoff=1002, initTime=0)
            # task.info()
            fms.addTaskToScheduler(task)
        # input()
    else:
        raise Exception(f"Incorrect number of tasks: {numberOfTasks}")
    
    t=0
    actualSimTime=0
    idleStep=0
    startTime = time.perf_counter()
    print('Start Time: ', datetime.now().strftime("%d/%m %H:%M:%S"))
    done = False
    while not done:
        # os.system('cls')
        print('#'*30)
        # print(f'Running Time: {timedelta(seconds=time.perf_counter()-startTime)} ({round(actualSimTime, 2)})' )
        done = fms.step(simTime=t)
        simLog = fms.getLog()
        taskLog = fms.getTaskLog()
        
        logger.log(data=simLog)
        logger.logTask(data=taskLog)
        
        if fms.isAllAGVIdle():
            idleStep += sampleTime
            if idleStep > 5 * sampleTime:
                nextTaskTime = fms.getNextTaskTime()
                print(nextTaskTime)
                if nextTaskTime is not None:
                    t = round(nextTaskTime - sampleTime, 2)
                    idleStep = 0
                    print(f'sim time fast fowarded to {t}!')
            else:
                t+=sampleTime
        else:
            t+=sampleTime
        
        actualSimTime += sampleTime
    
    # print("Task variable", vars(task))
    # print("AGV variable", vars(agv))
    print("Tasks done: ",fms.getTaskDone())
    print("Simulation done.") 
    print(f"Simulation Time used: {int(t/3600)}H {int((t%3600)/60)}M  {int((t%3600)%60)}S")
    print('AGV crashed: ', fms.getCrashedAGVid())
    print(f"Real Time used: {timedelta(seconds=time.perf_counter()-startTime)}")

if __name__ == '__main__':
    run()
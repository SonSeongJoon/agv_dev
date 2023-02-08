from doctest import master
from re import L
from agv import AGV
from scheduler import Scheduler
from dispatcher import Dispatcher
from router import Router
import numpy as np
import configparser
from math import ceil
import itertools
from  scipy.stats import rankdata

configFile = 'config.ini'

class FMS:
    def __init__(self, mapper, sampleTime, fixedPickUpPoint, fixedDropOffPoint, manualPoint):
        self.mapper = mapper
        self.fleet = []
        self.sampleTime = sampleTime
        self.scheduler = Scheduler()
        self.dispatcher = Dispatcher(mapper)
        self.router = Router(mapper)
        self.fixedPickUpPoint=fixedPickUpPoint
        self.fixedDropOffPoint=fixedDropOffPoint
        self.idlePoint= None
        self.crashedAGV = []
        self.crashedPairList = []
        self.crashedLocation = []
        self.crashTime = []
        self.locList = None
        self.posList = None
        self.pathList = None
        self.TAList = np.empty([0])
        self.freezeCounter = 0
        self.previousPos = np.empty([0])
        self.verbose = True 
        self.maxBreakingDistance = 0
        self.breakingMargin = 1
        self.conflictedAGVs = []
        self.previousConflictedAGVs = np.array([])
        self.manualPoint = manualPoint
        self.taskDone = 0
        self.log = {}
        self.taskLog = []
        self.retardingAGV = 0
        self.stopPointList = []
        
        self.ordinaryRestrictedPoints = self.fixedPickUpPoint.copy()
        self.ordinaryRestrictedPoints.extend(self.fixedDropOffPoint.copy())
        
        config = configparser.ConfigParser()
        config.read(configFile)
        self.mapLength = config.getint('MAP','width')
        self.gridSize = config.getfloat('MAP','gridSize')
        self.agvSize = config.getfloat('AGV','agvSize')
        
        if self.manualPoint:
            self.dropOffWaitingPointList = np.array(fixedDropOffPoint)
            self.dropOffWaitingPointList[:len(fixedDropOffPoint) - len(self.manualPoint)] = self.dropOffWaitingPointList[:len(fixedDropOffPoint) - len(self.manualPoint)] + self.mapLength
            self.dropOffWaitingPointList[len(fixedDropOffPoint) - len(self.manualPoint):] = self.dropOffWaitingPointList[len(fixedDropOffPoint) - len(self.manualPoint):] - 3
        else:
            self.dropOffWaitingPointList = np.array(fixedDropOffPoint) + self.mapLength
        self.pickupWaitingPointList = np.array(fixedPickUpPoint) - self.mapLength
        
        self.allPickAndDropPoints = np.append(np.array(fixedDropOffPoint), np.array(fixedPickUpPoint))
        
        self.crashMargin = self.agvSize-0.1

    def addAGV(self, number_of_agv, agvSPD, agvACL, agvRotateSPD, initPoint):
        """ 
        inipoint should be different for each AGV
        """
        if len(initPoint) != number_of_agv:
            raise ValueError("The number of initial points does not match the number of AGVs.")
        
        for i in range(number_of_agv):
            initPointCoord = self.mapper.pointConvertCoord(initPoint[i])
            self.fleet.append(AGV(id=i, initPos=initPoint[i], agvSPD=agvSPD, agvACL=agvACL, agvRotateSPD=agvRotateSPD, initCoord=initPointCoord, mapper=self.mapper, sampleTime=self.sampleTime))
            
        self.idlePoint = np.array(initPoint)
        self.locList = np.empty([len(self.fleet), 2])
        self.posList = np.empty([len(self.fleet)])
        self.nextPosList = np.empty([len(self.fleet)])
        self.destList = np.empty([len(self.fleet)])
        self.taskTargetList = np.empty([len(self.fleet)])
        self.pathList = np.empty([len(self.fleet)], dtype=np.object)
        self.resolvingAGVs = np.empty(shape=(0), dtype=int)
        
        
        self.maxBreakingDistance = self.fleet[0].maxBreakingDistance
        self.maxBreakingPoints = ceil(self.maxBreakingDistance / self.gridSize) + 1
        
        self.breakingPointList = np.empty([len(self.fleet), self.maxBreakingPoints + self.breakingMargin])
        
        
    def addTaskToScheduler(self, task):
        self.scheduler.addTask(task)
    
    def assignTask(self, task, agvID):
        self.dispatcher.assignTask(id=agvID, task=task, fleet=self.fleet)
        
    def isAllAGVIdle(self):
        for agv in self.fleet:
            if not agv.isIdle():
                return False
        return True
    def getTaskDone(self):
        return self.taskDone
    
    def assignPath(self, agvID):
        currentPos, dest = self.fleet[agvID].getCurrentPosandDest() 
        # restrictedPoint = np.array(self.ordinaryRestrictedPoints)
        # restrictedPoint = np.append(restrictedPoint, self.idlePoint)
        restrictedPoint = np.array(self.idlePoint)
        restrictedPoint = np.delete(restrictedPoint, np.where(restrictedPoint==currentPos))
        restrictedPoint = np.delete(restrictedPoint, np.where(restrictedPoint==dest))
        if self.fleet[agvID].isStopped():
            path = self.router.shortestPathWithRestriction(restrictedPoint=restrictedPoint, start=currentPos, dest=dest)
        else:
            path = self.router.shortestPathWithRestriction(restrictedPoint=restrictedPoint, start=currentPos, dest=dest, compulPoint= self.fleet[agvID].getNextPoint())
        
        if path:
            segmentPath = self.router.sortSegments(path.copy())
            self.fleet[agvID].assignPath(path, segmentPath)
            if len(self.fleet[agvID].path) > 10:
                print(f"AGV {agvID}: assgined new path {self.fleet[agvID].path[:10]} ({len(self.fleet[agvID].path) - 10} more points)")
            else:
                print(f"AGV {agvID}: assgined new path {self.fleet[agvID].path}")
        else:
            if self.fleet[agvID].isStopped():
                print(f"AGV {agvID}: No path available for now!")
            else:
                print(f"AGV {agvID}: No path available for now! stopping...")
                self.fleet[agvID].turnOnRetard()
        
    def getLocationList(self):
        for i, agv in enumerate(self.fleet):
            coord = agv.getCurrentCoord()
            self.locList[i] = coord
        
        return self.locList
    
    def getPosList(self):
        for i, agv in enumerate(self.fleet):
            pos = agv.getCurrentPos()
            self.posList[i] = int(pos)
            path = agv.getPath()
            if len(path) > 1: 
                self.nextPosList[i] = int(path[1])
            else:
                self.nextPosList[i] = np.nan
        return self.posList
    
    def getDestList(self):
        for i, agv in enumerate(self.fleet):
            pos = agv.getCurrentPosandDest()[1]
            if pos is not None:
                self.destList[i] = int(pos)
            else:
                self.destList[i] = pos
        return self.destList
    
    def getPathList(self):
        for i, agv in enumerate(self.fleet):
            path = agv.getPath() 
            self.pathList[i] = np.array(path)
        return self.pathList
    
    def getCollisionMatrix(self):
        numAgv = len(self.fleet)
        self.collisionMatrix = np.zeros((numAgv,numAgv))
        
        for i in range(numAgv-1):
            distanceList = np.sqrt(np.sum(np.square(self.locList - self.locList[i]), axis=1))
            distanceList[np.arange(0,i+1,1)] = np.nan
            self.collisionMatrix[i] = distanceList
        
        self.collisionMatrix[numAgv-1] = np.full((numAgv),np.nan)
        
        if self.crashedPairList:
            for pair in self.crashedPairList:
                self.collisionMatrix[pair[0],pair[1]] = np.nan
        return self.collisionMatrix
    
    def getPathPointMatrix(self, cutoff):
        self.pathPointMatrix = np.empty([len(self.fleet), cutoff])
        self.getPathList()
        
        for i, path in enumerate(self.pathList):
            if not path.all():
                self.pathPointMatrix[i] = np.full(cutoff, np.nan)
            elif len(path) >= cutoff:
                self.pathPointMatrix[i] = path[0:cutoff]
            elif len(path) == 0:
                self.pathPointMatrix[i] = np.full(cutoff, np.nan)
                self.pathPointMatrix[i][0] = self.fleet[i].getCurrentPos()
            else:
                self.pathPointMatrix[i] = np.append(path, np.full(cutoff-len(path),np.nan))
    
    def isToManualPoint(self, agv):
        return agv.getTaskStartDest()[1] in self.manualPoint
        
    
    def getNextTaskTime(self):
        return self.scheduler.getNextTaskTime()
    
    def assignWaitingPoint(self, agv):
        start, dest = agv.getTaskStartDest()
        if agv.isProcessing() or agv.isPickingUp():
            dest = start
            destIndex = np.where(np.array(self.fixedPickUpPoint)==dest)
            waitingPoint = int(self.pickupWaitingPointList[destIndex])
        else:
            destIndex = np.where(np.array(self.fixedDropOffPoint)==dest)
            waitingPoint = int(self.dropOffWaitingPointList[destIndex])
            
        destList = self.getDestList()
        
        def checkWaitingPoint(waitingPoint):
            if waitingPoint in destList or waitingPoint in self.posList:
                if agv.isProcessing() or agv.isPickingUp():
                    waitingPoint -= self.mapLength
                else:
                    if self.isToManualPoint(agv):
                        waitingPoint -= 1
                    else:
                        waitingPoint += self.mapLength
                waitingPoint = checkWaitingPoint(waitingPoint)
            return waitingPoint
        
        waitingPoint = checkWaitingPoint(waitingPoint)
        
        if agv.getWaitingPoint():
            if self.isToManualPoint(agv) and agv.isTransferring():
                if agv.getWaitingPoint() > waitingPoint :
                    return False
                else:
                    agv.transitToWaitingPoint(waitingPoint)
                    return True
            
            if agv.getWaitingPoint() < waitingPoint and agv.isTransferring():
                return False
            elif agv.getWaitingPoint() > waitingPoint and agv.isPickingUp():
                return False
            else:
                agv.transitToWaitingPoint(waitingPoint)
                return True
        else:
            agv.transitToWaitingPoint(waitingPoint)
            return False
    
    def approachDropoff(self, agv):
        currentPos = agv.getCurrentPos()
        if agv.isPickingUp():
            dropoff = agv.task.start
            atFirstWaitingPoint = currentPos in self.pickupWaitingPointList
            lineCheck = np.arange(dropoff, agv.getCurrentPosandDest()[0], -self.mapLength) 
        else:
            dropoff = agv.task.dest
            atFirstWaitingPoint = currentPos in self.dropOffWaitingPointList
            if self.isToManualPoint(agv):
                lineCheck = np.arange(dropoff, agv.getCurrentPosandDest()[0], -1) 
            else:
                lineCheck = np.arange(dropoff, agv.getCurrentPosandDest()[0], self.mapLength)
        
        self.getPosList()
        toCheckMatrix = np.delete(self.posList, agv.ID, axis=0)
        
        def getFrontWaitingPoint(pickup):
            if pickup:
                return agv.getCurrentPos() + self.mapLength
            elif self.isToManualPoint(agv):
                return agv.getCurrentPos() + 1
            else:
                return agv.getCurrentPos() - self.mapLength
        
        if atFirstWaitingPoint and not agv.isApproaching():
            if np.isin(toCheckMatrix, lineCheck).any():
                # if not agv.isRetarding():
                print(f'AGV {agv.ID}: Drop-off point [{dropoff}] area is busy, stopping at waiting point [{agv.currentPos}] ')
                agv.dest = agv.getWaitingPoint()
                agv.turnOnRetard()
            else:
                if agv.isResolvingConflicts():
                    print(f'AGV {agv.ID}: Resolving conflicts. Cannot proceed to end point [{dropoff}]')
                    agv.turnOnRetard()
                else:
                    print(f'AGV {agv.ID}: Proceeding to end point [{dropoff}]')
                    agv.dest = dropoff
                    agv.turnOffRetard()
                    agv.approachEndPoint()
        elif not atFirstWaitingPoint and agv.isApproaching():
            pass
        elif atFirstWaitingPoint and agv.isApproaching():
            pass
        elif not atFirstWaitingPoint and not agv.isApproaching():
            if agv.currentPos == agv.getWaitingPoint():
                if self.assignWaitingPoint(agv):
                    print(f'AGV {agv.ID}: assigned to NEW waiting point [{agv.getWaitingPoint()}] 1')
                    agv.dest = agv.getWaitingPoint()
                    agv.turnOnRetard()
                elif getFrontWaitingPoint(agv.isPickingUp()) not in self.posList or agv.ID not in self.conflictedAGVs: 
                    if agv.isResolvingConflicts():
                        print(f'AGV {agv.ID}: Resolving conflicts. Cannot proceed to NEW waiting point [{agv.getWaitingPoint()}] 2')
                        agv.turnOnRetard()
                    else:
                        print(f'AGV {agv.ID}: Proceeding to NEW waiting point [{agv.getWaitingPoint()}] 2')
                        agv.dest = agv.getWaitingPoint()
                else:
                    print(f'AGV {agv.ID}: queuing at waiting point [{agv.getWaitingPoint()}]')
                    agv.dest = agv.getWaitingPoint()
                    agv.turnOnRetard()
            else:
                if agv.isResolvingConflicts():
                    print(f'AGV {agv.ID}: Resolving conflicts. Cannot proceed to NEW waiting point [{agv.getWaitingPoint()}]')
                else:
                    print(f'AGV {agv.ID}: Proceeding to NEW waiting point [{agv.getWaitingPoint()}]')
                    if getFrontWaitingPoint(agv.isPickingUp()) in self.posList or agv.ID in self.conflictedAGVs: 
                        # print('front have agv')
                        agv.turnOnRetard()
                    else:
                        agv.turnOffRetard()
                    
                    agv.dest = agv.getWaitingPoint()
                    self.assignPath(agvID=agv.ID)
    
    def getTaskTargetList(self):
        for i, agv in enumerate(self.fleet):
            if agv.isPickingUp():
                self.taskTargetList[i] = agv.task.start
            elif agv.isTransferring():
                self.taskTargetList[i] = agv.task.dest
            else:
                self.taskTargetList[i] = None
        return self.taskTargetList
        
    def sortWaitingPoint(self, verbose=False):
        self.getTaskTargetList()
        
        u, c = np.unique(self.taskTargetList, return_counts=True)
        conflictedDestPoints = u[c > 1]
        conflictedDestPoints = np.delete(conflictedDestPoints, np.isnan(conflictedDestPoints))
        
        if conflictedDestPoints.any():
            if verbose:
                print('----Sorting waiting point----')
                print('conflictedDestPoints', conflictedDestPoints)
            for conflictedPoint in conflictedDestPoints:
                # get conflicted AGV list
                conflictedAGVids = np.where(self.taskTargetList == conflictedPoint)[0]
                conflictedPoint_coord = self.mapper.pointConvertCoord(conflictedPoint)
                
                distanceList = np.empty([len(conflictedAGVids)])
                
                for i, agvID in enumerate(conflictedAGVids):
                    agvCoord = self.fleet[agvID].getCurrentCoord()
                    # not true distance, square root wont make a difference of the result
                    distanceList[i] = (agvCoord[0]-conflictedPoint_coord[0])**2 + (agvCoord[1]-conflictedPoint_coord[1])**2  
                
                rankedDistance = rankdata(distanceList) - 1
                
                if verbose:
                    print('shared point:', conflictedPoint)
                    print('shared point conflict AGV:', conflictedAGVids)
                    print('shared point rankedDistance:', rankedDistance)
                
                if self.fleet[conflictedAGVids[0]].isPickingUp():
                    firstWaitingPoint = self.pickupWaitingPointList[self.fixedPickUpPoint.index(conflictedPoint)]
                    lineCheck = np.arange(firstWaitingPoint, firstWaitingPoint - len(rankedDistance) * self.mapLength, -self.mapLength) 
                elif self.fleet[conflictedAGVids[0]].isTransferring():
                    firstWaitingPoint = self.dropOffWaitingPointList[self.fixedDropOffPoint.index(conflictedPoint)]
                    if conflictedPoint in self.manualPoint:
                        lineCheck = np.arange(firstWaitingPoint, firstWaitingPoint - len(rankedDistance), -1) 
                    else:
                        lineCheck = np.arange(firstWaitingPoint, firstWaitingPoint + len(rankedDistance) * self.mapLength, self.mapLength) 
                else:
                    continue
                
                for i, agvID in enumerate(conflictedAGVids):
                    agv = self.fleet[agvID]
                    agvWaitingPoint = agv.getWaitingPoint()
                    correctWaitingPoint = lineCheck[int(rankedDistance[i])]
                    if agvWaitingPoint != correctWaitingPoint and correctWaitingPoint not in self.posList:
                        if verbose:
                            print(f'AGV {agvID} waiting point', agvWaitingPoint,'correct waiting point', correctWaitingPoint)
                            print('orginal path', agv.getPath())
                        agv.transitToWaitingPoint(target=correctWaitingPoint, correction=True)
                        if agv.isStopped:
                            self.assignPath(agvID=agv.ID)
                        else:
                            self.assignRestrictedPath(agvID=agv.ID, restrictedPointList=[], compulPoint=agv.getPath()[1])
                        if verbose:
                            print('correct path', agv.getPath())
    
    def assignRestrictedPath(self, agvID, restrictedPointList, compulPoint=None, verbose=False):
        currentPos, dest = self.fleet[agvID].getCurrentPosandDest()
        orginalPath = self.fleet[agvID].getPath()
        # restrictedPoint = np.array(self.ordinaryRestrictedPoints)
        # restrictedPoint = np.append(restrictedPoint, restrictedPointList)
        
        restrictedPoint = np.array(restrictedPointList)
        restrictedPoint = np.append(restrictedPoint, self.idlePoint)
        restrictedPoint = np.append(restrictedPoint, self.stopPointList)
        restrictedPoint = np.append(restrictedPoint, self.nextPosList)
        restrictedPoint = np.delete(restrictedPoint, np.where(restrictedPoint==currentPos))
        restrictedPoint = np.delete(restrictedPoint, np.where(restrictedPoint==dest))
        restrictedPoint = np.unique(restrictedPoint[np.logical_not(np.isnan(restrictedPoint))])
        restrictedPoint = np.delete(restrictedPoint, np.where(restrictedPoint==compulPoint))
        
        if verbose:
            print("Assigning restricted path")
            print(f"Restriced point:{restrictedPoint}")
        
        path = self.router.shortestPathWithRestriction(restrictedPoint, currentPos, dest, compulPoint)
        
        if verbose:
            print(f'Path: {path}')
        
        if path:
            if np.isin(path, restrictedPoint).any():
                if verbose: 
                    print(f"AGV {agvID}: path has conflict points still")
                return False
            if orginalPath == path:
                if verbose: 
                    print(f"AGV {agvID}: path did not change")
                return False
            segmentPath = self.router.sortSegments(path.copy())
            self.fleet[agvID].assignPath(path, segmentPath)
            if verbose:
                print(f"AGV {agvID}: Assigned new restricted path ", self.fleet[agvID].path)
            return True
        else:
            if verbose: 
                print(f"AGV {agvID}: cannot generate path")
            return False
    
    def checkCollisonAdvisory(self):
        """ 
        To be documented.
        """
        # for the record, this part is harder than my life
        # it's really so hard that I got stuck for almost 3 months. I'm shattered.
        # finally it took around 5 months to fix the whole detection, you're welcome
        
        self.conflictedPairs = np.empty([0,2])
        
        def checkDuplicateConflictedPair(conflictedAGVs):
            for pair in self.conflictedPairs:
                if (np.isin(conflictedAGVs,pair)).all():
                    return True
            return False
        
        def checkClearedPair():
            clearedPairs = np.empty([0,2])
            
            for pair in self.previousConflictedAGVs:
                matched = False
                for pair2 in self.conflictedPairs:
                    if (np.isin(pair2, pair)).all():
                        matched=True
                        break
                if not matched:
                    clearedPairs = np.append(clearedPairs, np.array([pair]), axis=0)
            
            return clearedPairs
        
        for agv in self.fleet:
            if agv.isIdle(): 
                self.breakingPointList[agv.ID] = np.append(np.array([agv.currentPos]),np.full(len(self.breakingPointList[agv.ID]) -1,np.nan))
                continue
            
            posCheckPoints = max(ceil(agv.breakingDistance / self.gridSize),1) + 1 + self.breakingMargin
            if posCheckPoints >len(agv.getPath()):
                posCheckPoints = len(agv.getPath())
            # print('posCheckPoints', posCheckPoints)
            self.breakingPointList[agv.ID] = np.append(np.array(agv.getPath()[0:posCheckPoints]), np.full(self.maxBreakingPoints + self.breakingMargin - posCheckPoints,np.nan))
        
        u, c = np.unique(self.breakingPointList, return_counts=True)
        conflictedPoints = u[c > 1]
        conflictedPoints = np.delete(conflictedPoints, np.isnan(conflictedPoints))
        
        if conflictedPoints.any():
            for conflictedPoint in conflictedPoints:
                conflictedAGVs = np.unique(np.where(self.breakingPointList==conflictedPoint)[0])
                if len(conflictedAGVs) == 1 : continue
                if len(conflictedAGVs) > 2: # special case for AGV > 2
                    conflictedAGVPairs = np.array(list(itertools.combinations(conflictedAGVs,2)))
                    for pair in conflictedAGVPairs:
                        if not checkDuplicateConflictedPair(pair):
                            self.conflictedPairs = np.append(self.conflictedPairs, np.array([pair]), axis=0)
                    continue
                if np.isin(conflictedAGVs, self.resolvingAGVs).all():
                    if not checkDuplicateConflictedPair(conflictedAGVs):
                        self.conflictedPairs = np.append(self.conflictedPairs, np.array([conflictedAGVs]), axis=0)
                    continue
                if not checkDuplicateConflictedPair(conflictedAGVs):
                    
                    self.conflictedPairs = np.append(self.conflictedPairs, np.array([conflictedAGVs]), axis=0)
            
            for pair in self.conflictedPairs:
                pair = pair.astype(int)
                for agvID in pair:
                    self.fleet[agvID].addConflict(agvID=pair.tolist())
            # print('conflicted pairs', self.conflictedPairs)
        
        self.conflictedAGVs = np.unique(self.conflictedPairs)
        clearedAGVs = checkClearedPair()
        if clearedAGVs.any():
            for pairID in clearedAGVs:
                agvID1 = pairID[0]
                agvID2 = pairID[1]
                self.fleet[int(agvID1)].removeConflict(agvID=int(agvID2))
                self.fleet[int(agvID2)].removeConflict(agvID=int(agvID1))
                self.resolvingAGVs = np.delete(self.resolvingAGVs, np.where(self.resolvingAGVs==agvID1))
                self.resolvingAGVs = np.delete(self.resolvingAGVs, np.where(self.resolvingAGVs==agvID2))
        self.previousConflictedAGVs = self.conflictedPairs
        
    ############################################################################################################
    ############################################################################################################
    ############################################################################################################
    ############################################################################################################
    ############################################################################################################
        
    def resolveConflicts(self):
        """ 
        To be documented
        """
        # I don't even know what's the number of attempt now, i think it's 5, 6? and I really wanna go die if it's not working. god save the algorithm
        # It didnt work for the 7th time, so did the 8th - 20th i guess. It's now countless time and it sort of works now.
        
        def commandStartStop(goAGV, stopAGV):
            if not self.conflictAtNextPoint(agv=goAGV, margin=2):
                goAGV.turnOffRetard()
                stopAGV.turnOnRetard()
                stopAGV.addResolvingList(agvID=goAGV.ID)
                goAGV.addResolvingList(agvID=stopAGV.ID)
                return True
            else:
                print(f'AGV {goAGV.ID} Cannot move')
                goAGV.turnOnRetard()
                stopAGV.turnOnRetard()
                stopAGV.addResolvingList(agvID=goAGV.ID)
                goAGV.addResolvingList(agvID=stopAGV.ID)
                return False
    
        self.getPathList()
        
        for pair in self.conflictedPairs:
            agv1 = self.fleet[int(pair[0])]
            agv2 = self.fleet[int(pair[1])]
            
            agv1_path = self.breakingPointList[int(pair[0])]
            agv2_path = self.breakingPointList[int(pair[1])]
            combinedPath = np.append(agv1_path, agv2_path)
            u, c = np.unique(combinedPath, return_counts=True)
            conflictedPoints = u[c > 1]
            
            # check if it has been resolving
            # agv1_resolvingList = agv1.getResolvingList()
            # agv2_resolvingList = agv2.getResolvingList()
            # agv1_conflictList = agv1.getConflictList()
            # agv2_conflictList = agv2.getConflictList()
            
            if (agv1.isQueuing() or agv1.isApproaching()):
                print(f"AGV {agv1.ID} is queuing or approaching")
                commandStartStop(goAGV=agv1, stopAGV= agv2)
                continue
            elif (agv2.isQueuing() or agv2.isApproaching()):
                print(f"AGV {agv2.ID} is queuing or approaching")
                commandStartStop(goAGV=agv2, stopAGV=agv1)
                continue
            elif agv1.isRetarding() and agv2.isRetarding():
                # print(f"AGV {agv1.ID} and AGV {agv2.ID} both are retarding")
                pass
            else:
                if not agv1.isResolvingConflicts():
                    agv1.turnOnRetard()
                if not agv2.isResolvingConflicts():
                    agv2.turnOnRetard()
            
            def assignStopPoint(agv, index, conflict=False):
                i = 1
                if conflict:
                    if agv.getStopPoint() is not None:
                        previousStopPoint = agv.getStopPoint()
                
                while True:
                    stopPoint = agv.path[index-i]
                    if (index - 1) <= 0:
                        agv.assignStopPoint(stopPoint=None)
                        return False
                    elif stopPoint not in self.stopPointList:
                        if conflict: 
                            if stopPoint == previousStopPoint:
                                i += 1
                            else:
                                agv.assignStopPoint(stopPoint=stopPoint)
                                return True
                        else:
                            agv.assignStopPoint(stopPoint=stopPoint)
                            return True
                    else:
                        i += 1
            
            # assign stop point
            agv1_conflictPointIndex = np.inf
            agv2_conflictPointIndex = np.inf
            conflictedPoints = conflictedPoints[np.logical_not(np.isnan(conflictedPoints))]
            for conflictedPoint in conflictedPoints:
                agv1_conflictPointIndex = min(agv1_conflictPointIndex, np.where(agv1_path==conflictedPoint)[0][0])
                agv2_conflictPointIndex = min(agv2_conflictPointIndex, np.where(agv2_path==conflictedPoint)[0][0])
            
            # print('agv1 path**', agv1.getPath())
            # print('agv2 path**', agv2.getPath())
            # print('agv1 SP',agv1.getStopPoint())
            # print('agv2 SP', agv2.getStopPoint())
            
            if not agv1.getStopPoint() or agv1.getStopPoint() not in agv1.getPath():
                assignStopPoint(agv=agv1, index=agv1_conflictPointIndex)
            if not agv2.getStopPoint() or agv2.getStopPoint() not in agv2.getPath():
                assignStopPoint(agv=agv2, index=agv2_conflictPointIndex)
            
            if agv1.getStopPoint() == agv2.getStopPoint() and agv1.getStopPoint() is not None and agv2.getStopPoint() is not None:
                assignStopPoint(agv=agv1, index=agv1_conflictPointIndex, conflict=True)
                assignStopPoint(agv=agv2, index=agv2_conflictPointIndex, conflict=True)
            
            if agv1.getStopPoint() is None and agv2.getStopPoint() is None:
                print('None stop point')
                if not agv1.isStopped() and not agv2.isStopped():
                    print('Stopping both due to no stop point')
                    agv1.turnOnRetard()
                    agv2.turnOnRetard()
                    continue
                
            
            print("*"*20)
            print('conflictedPoints', conflictedPoints)
            print('conflict AGV', pair)
            # print('agv1 path', agv1.getPath()[:5])
            # print('agv2 path', agv2.getPath()[:5])
            print('agv1 stop point:', agv1.stopPoint, 'speed', agv1.speed)
            print('agv2 stop point:', agv2.stopPoint, 'speed', agv2.speed)
            
            
            ## identify AGV
            '''
            |           |   EVEN |   ODD
            |Vertical   |    N  |     S
            |Horizontal |    W  |     E
            '''
            '''
            E(-> +)   go first
            E(+ ->)   safe for N/S
            W (+ <-)  go first
            W (<- +)  safe for N/S
            '''
            # print(f'AGV {agv1.ID} stopping range', agv1_path)
            # print(f'AGV {agv2.ID} stopping range', agv2_path)
            # print(f'AGV {agv1.ID} pos {agv1.getCurrentPos()} break {agv1.isRetarding()}')
            # print(f'AGV {agv2.ID} pos {agv2.getCurrentPos()} break {agv2.isRetarding()}')
            
            agv1_coord = agv1.getCurrentCoord()
            agv2_coord = agv2.getCurrentCoord()
            
            # use the point to determine the direction
            if agv1_conflictPointIndex != 0:
                dir = agv1_path[agv1_conflictPointIndex] - agv1_path[agv1_conflictPointIndex-1]
            else:
                dir = agv1_path[1] - agv1_path[0]
            if dir == 1 : 
                agv1_dir = 'E'
            elif dir == -1:
                agv1_dir = 'W'
            elif dir > 0:
                agv1_dir = 'N'
            else:
                agv1_dir = 'S'
            
            if agv2_conflictPointIndex != 0:
                dir = agv2_path[agv2_conflictPointIndex] - agv2_path[agv2_conflictPointIndex-1]
            else:
                dir = agv2_path[1] - agv2_path[0]
            if dir == 1 : 
                agv2_dir = 'E'
            elif dir == -1:
                agv2_dir = 'W'
            elif dir > 0:
                agv2_dir = 'N'
            else:
                agv2_dir = 'S'
            
            if agv1.isStopped() and agv2.isStopped():
                ## check if it's idle, direct change route
                if agv1.isIdle() or agv1.isCrashed():
                    masterAGVCompulPoint = agv2.getNextPoint()
                    restrictedPointList = [agv1.getCurrentPos()]
                    if self.assignRestrictedPath(agvID=agv2.ID, restrictedPointList=restrictedPointList, compulPoint=None, verbose=False):
                        print(f"AGV {agv2.ID} assigned restricted path due to idle/queuing AGV")
                        continue
                    else:
                        print(f"AGV {agv2.ID} Stopping due to idle AGV")
                        agv1.turnOnRetard()
                        continue
                elif agv2.isIdle() or agv2.isCrashed():
                    masterAGVCompulPoint = agv1.getNextPoint()
                    restrictedPointList = [agv2.getCurrentPos()]
                    if self.assignRestrictedPath(agvID=agv1.ID, restrictedPointList=restrictedPointList, compulPoint=None, verbose=False):
                        print(f"AGV {agv1.ID} assigned restricted path due to idle/queuing AGV")
                        continue
                    else:
                        print(f"AGV {agv1.ID} Stopping due to idle AGV")
                        agv1.turnOnRetard()
                        continue
                
                
                if agv1.getCurrentPos() in conflictedPoints: 
                    if commandStartStop(goAGV=agv1, stopAGV=agv2):
                        print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP  [A3_1]')
                    elif self.assignRestrictedPath(agvID=agv2.ID, restrictedPointList=self.posList, verbose=False):
                        print(f'Resolve AGV {agv2.ID} change path  [A3_2]')
                    else:
                        print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP  [A3n]')
                    continue
                elif agv2.getCurrentPos() in conflictedPoints:
                    if commandStartStop(goAGV=agv2, stopAGV=agv1):
                        print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO  [A2_1]')
                    elif self.assignRestrictedPath(agvID=agv1.ID, restrictedPointList=self.posList, verbose=False):
                        print(f'Resolve AGV {agv1.ID} change path  [A2_2]')
                    else:
                        print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP  [A2n]')
                    continue
                
                if agv1_dir == 'N' or agv1_dir == 'S':
                    if agv2_dir == 'E':
                        if agv2_coord[0] <= agv1_coord[0]:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [cross 1]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [cross 1n]')
                        else:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [cross 2]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [cross 2n]')
                        continue
                    elif agv2_dir == 'W':
                        if agv2_coord[0] >= agv1_coord[0]:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [cross 3]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [cross 3n]')
                        else:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [cross 4]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [cross 4n]')
                        continue
                
                elif agv2_dir == 'N' or agv2_dir == 'S':
                    if agv1_dir == 'E':
                        if agv1_coord[0] <= agv2_coord[0]:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [cross 5]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [cross 5n]')
                        else:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [cross 6]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [cross 6n]')
                        continue
                    elif agv1_dir == 'W':
                        if agv2_coord[0] <= agv1_coord[0]:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [cross 8]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [cross 8n]')
                            
                        else:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [cross 7]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [cross 7n]')
                        continue
                
                if agv1_dir == agv2_dir:
                    # check NESW
                    if agv1_dir == 'N':
                        if agv1_coord[1] > agv2_coord[1]:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 1]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 1n]')
                        else:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [pursue 2]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 2n]')
                    elif agv1_dir == 'E':
                        if agv1_coord[0] > agv2_coord[0]:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 3]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 3n]')
                        else:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [pursue 4]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 4n]')
                    elif agv1_dir == 'S':
                        if agv1_coord[1] < agv2_coord[1]:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 5]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 5n]')
                        else:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [pursue 6]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 6n]')
                    else: # W
                        if agv1_coord[0] < agv2_coord[0]:
                            if commandStartStop(goAGV=agv1, stopAGV=agv2):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} GO   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 7]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 7n]')
                        else:
                            if commandStartStop(goAGV=agv2, stopAGV=agv1):
                                print(f'Resolve AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} GO [pursue 8]')
                            else:
                                print(f'Not resolved AGV {agv1.ID} direction {agv1_dir} STOP   AGV {agv2.ID} direction {agv2_dir} STOP [pursue 8n]')
                    continue
                
                print(f'Resolve agv1 {agv1_dir} agv2 {agv2_dir} no immediate threats')
                continue
            else:
                agv1.turnOnRetard()
                agv2.turnOnRetard()
                print('Both stopping')
            
            ## **************************
        
        return
    
    def collisonCheck(self, simTime):
        self.getPosList()
        self.getLocationList()
        self.getCollisionMatrix()
        check = self.collisionMatrix <= self.crashMargin
        
        if check.any():
            crashedAGV = np.where(check)
            newCrashed = np.unique(np.concatenate((np.where(check)))).tolist()
            
            for i in range(len(crashedAGV[0])):
                agv1, agv2 = crashedAGV[0][i], crashedAGV[1][i]
                crashedPair = [agv1, agv2]
                
                if crashedPair not in self.crashedPairList:
                    locAGV1 = self.locList[agv1]
                    locAGV2 = self.locList[agv2]
                    loc = (locAGV1 + locAGV2) / 2
                    self.crashedLocation.append(loc.tolist())
                    self.crashedAGV.extend(newCrashed)
                    self.crashedAGV = list(set(self.crashedAGV))
                    self.crashedPairList.append(crashedPair)
                    self.crashTime.append(simTime)
                    print('*'*100)
                    print("CRASHED!!! AGV: ", crashedPair)
                    print('Task done:', self.taskDone)
                    for pair in crashedPair:
                        print(self.breakingPointList[pair])
                        agv = self.fleet[pair]
                        print(f"AGV{agv.ID}: speed {round(agv.speed,3)} retard {agv.isRetarding()} location {agv.currentPos} stopPoint {agv.stopPoint} coord {agv.currentCoord} posCoord {self.mapper.pointConvertCoord(agv.currentPos)} path {agv.path[:5]} dest {agv.dest} ResolvingConflicts {agv.isResolvingConflicts()} conflictList {agv.conflictList} resolvingList {agv.resolvingList}")
                    
                    # input("Press to Continue...")
                    
                
            for id in self.crashedAGV:
                agv = self.fleet[id]
                if not agv.isCrashed():
                    agv.setCrashed()
            
            return True
            
    def getCrashedAGVid(self):
        return self.crashedAGV
    
    def getCrashedAGVLocation(self):
        return self.crashedLocation
    
    def getCrashTime(self):
        return self.crashTime

    def isAllCrashed(self):
        for agv in self.fleet:
            if not agv.isCrashed():
                return False
        return True
    
    def getLog(self):
        return self.log
    
    def getTaskLog(self):
        return self.taskLog
    
    def conflictAtNextPoint(self, agv, margin):
        nextPosList = self.breakingPointList.copy()
        nextPosList = np.delete(nextPosList, agv.ID, axis=0)
        nextPosList = nextPosList[:,:margin]
        
        currentPosList = nextPosList[:,:1]
        if agv.getNextPoint() in currentPosList:
            targets = np.where(self.breakingPointList==agv.getNextPoint())[0]
            targets = np.delete(targets, np.where(targets==agv.ID))
            print(f'AGV {agv.ID} Blocking AGV (Stopped at spot):', targets)
            return True
        
        if agv.getNextPoint() in self.stopPointList:
            targets = np.where(self.breakingPointList==agv.getNextPoint())[0]
            targets = np.delete(targets, np.where(targets==agv.ID))
            print(f'AGV {agv.ID} Blocking AGV (Stop point):', targets)
            return True
        
        if agv.getNextPoint() in nextPosList and (not agv.isQueuing() or not agv.isApproaching()):
            targets = np.where(self.breakingPointList==agv.getNextPoint())[0]
            targets = np.delete(targets, np.where(targets==agv.ID))
            for target in targets:
                if not self.fleet[target].isStopped():
                    print(f'AGV {agv.ID} Blocking AGV (moving):', target)
                    return True
                
            print(f'AGV {agv.ID} Blocking AGV (stopped not at spot):', targets)
            return False
        else:
            # print(f'AGV {agv.ID} No conflict')
            return False
    
    def step(self, simTime):
        simTime = round(simTime, 2)
        self.log.clear()
        self.taskLog.clear()
        self.log['time'] = simTime
        self.log['agv'] = []
        updated = False
        # print('Runtime: ', simTime)
        # self.scheduler.showNextTask()
        # print('Remaining tasks: ', self.scheduler.getRemainingTasks(), f"({round((1 - (self.scheduler.getRemainingTasks()/ self.scheduler.getTotalNumberOfTasks()))*100,1)}%)")
        # print('Tasks on idle: ', len(self.scheduler.showAvailableTask()))
        # print('Available AGVs: ', len(self.idlePoint))
        # print('Task completed: ', self.taskDone)
        # print('Conflicted AGV: ', len(self.stopPointList))
        
        
        # dispatch task to agv
        self.scheduler.update(simTime)
        while not updated:
            if self.scheduler.isEmpty() or self.dispatcher.hasIdleAGV(self.fleet) is None:
                break
            if not self.scheduler.isEmpty():
                taskLoc = self.scheduler.getFirstTaskPickUpLocation()
                taskCoord = self.mapper.pointConvertCoord(point=taskLoc)
                agvID = self.dispatcher.findIdleAGV(fleet=self.fleet, method='shortestDistance',  taskLocation=taskCoord)
                if agvID is not None:
                    task = self.scheduler.getTask()
                    self.dispatcher.assignTask(id=agvID, task=task, fleet=self.fleet)
                    
                else:
                    print('No free AGV for task')
                    break
        
        # print("-"*10)
        self.getPosList()
        self.router.updatePosList(posList=self.posList)
        self.sortWaitingPoint(verbose=False)
        self.checkCollisonAdvisory()
        self.resolveConflicts()
        self.retardingAGV = 0
        self.stopPointList.clear()
        # step agv
        for agv in self.fleet:
            print('next point', agv.nextPoint)
            print('AGV pos', agv.currentPos)
            print('AGV path', agv.path)
            print('AGV segment path', agv.segmentPath)
            print('SPD', agv.speed)
            print('retard', agv.retard)
            if agv.isQueuing():
                self.approachDropoff(agv)
            if agv.isRequestingWaitingPoint():
                self.assignWaitingPoint(agv)
            if agv.isRequestingPath():
                self.assignPath(agv.ID)
            if self.conflictAtNextPoint(agv=agv, margin=3):
                agv.turnOnRetard()
            if agv.getStopPoint() in self.stopPointList:
                agv.turnOnRetard()
            agv.step(self.sampleTime)
            if agv.isIdle() and agv.getCurrentPos() in self.fixedDropOffPoint :
                agv.transit() # back to init point
                self.taskDone +=1
                
            if agv.isIdle() and agv.getCurrentPos() not in self.idlePoint:
                self.idlePoint = np.append(self.idlePoint, agv.getCurrentPos())
            elif not agv.isIdle() and agv.getCurrentPos()  in self.idlePoint:
                self.idlePoint = np.delete(self.idlePoint, np.where(self.idlePoint==agv.getCurrentPos()))
            if agv.getStopPoint() is not None:
                self.stopPointList.append(agv.getStopPoint())
            if agv.isRequiringLogTask():
                agv.task.logTime(logTime=simTime)
                agv.comepleteLogTime()
                if agv.task.isDelivered():
                    self.taskLog.append({
                        "id" : agv.task.taskID, 
                        "agv" : agv.ID,
                        "initTime": agv.task.timelog['initTime'],
                        "assignTime": agv.task.timelog['assignTime'],
                        "pickupTime": agv.task.timelog['pickupTime'],
                        "comepleteTime": agv.task.timelog['comepleteTime'],
                    })
                    agv.clearTask()
                
            self.log["agv"].append({
                "id" : agv.ID, 
                "status": agv.statusID,
                "currentCoord": agv.currentCoord.tolist(),
                "speed":agv.speed,
                "retard":agv.retard,
                "orientation": agv.orientation
            })
            
            ## For debugging 
            # if agv.ID in [31, 40]:
            #     if agv.path:
            #         log = f"t {round(simTime, 2)} AGV{agv.ID}: speed {round(agv.speed,3)} retard {agv.isRetarding()} stopPoint {agv.stopPoint} location {agv.currentPos} path {agv.path[:5]}( {max(0, len(agv.path) - 5)}) queue{agv.isQueuing()} approach{agv.isApproaching()} dest {agv.dest} conflictList {agv.conflictList} resolvingList {agv.resolvingList}"
            #         with open('agv.txt', 'a') as f:
            #             f.write(str(log)+'\n')
            
            # # DEBUG
            # if agv.ID == 6:
            # print(f"AGV{agv.ID}: speed {round(agv.speed,3)} retard {agv.isRetarding()} location {agv.currentPos} path {agv.path} dest {agv.dest} ResolvingConflicts {agv.isResolvingConflicts()} conflictList {agv.conflictList} resolvingList {agv.resolvingList}")
        
        self.TAList = np.empty([0])
        
        agv_crashed = False
        agv_crashed = self.collisonCheck(simTime=simTime)
        self.log["crashedAGV"] = self.getCrashedAGVid()
        self.log["crashedLocation"] = self.getCrashedAGVLocation()
        self.log["crashTime"] = self.getCrashTime()
        self.log["taskDone"] = self.getTaskDone()
        
        # End simulation based on situations below
        if agv_crashed:
            return True
        if self.scheduler.finishedAllTasks() and self.isAllAGVIdle():
            print('All tasks finished.')
            return True
        elif self.isAllCrashed():
            print("All AGVs crashed.")
            return True
        else:
            if len(self.previousPos) == 0:
                self.previousPos = self.posList.copy()
            
            if (np.isin(self.previousPos, self.posList)).all():
                self.freezeCounter += self.sampleTime 
                if self.freezeCounter > 100 * self.sampleTime :
                    print("Everything freezed")
                    print(self.posList)
                    # print(self.pathList)
                    return True
            else:
                self.previousPos = self.posList.copy()
                self.freezeCounter = 0
            
        return False
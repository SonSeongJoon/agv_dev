from enum import Enum
from math import sqrt, ceil

class AGVStatus(Enum):
    IDLE = 1
    TASKRECEIVED = 2
    PROCESSING = 3
    PICKINGUP = 4
    TRANSFERRING = 5
    TRANSIT= 6
    CRASHED = 99
    
    
class AGV:
    def __init__(self, id, initPos, agvSPD, agvACL, agvRotateSPD, initCoord, mapper, sampleTime):
        self.ID=id
        self.sampleTime = sampleTime
        self.status = AGVStatus.IDLE
        self.statusID = AGVStatus.IDLE.value
        self.currentCoord = initCoord
        self.currentPos = initPos
        self.task = None
        self.start = self.currentPos
        self.initPoint = initPos
        self.dest = None
        self.path = []
        self.segmentPath = []
        self.nextPoint = None
        self.maxSPD = agvSPD
        self.accel = agvACL  # assuming acceleration = deceleration 
        self.rotateSPD = agvRotateSPD
        self.speed = 0
        self.retard = False
        self.mapper = mapper
        self.remainingDistance = 0
        self.retard = False
        self.retardRequest = False
        self.pathRequest = False
        self.direction = None
        self.checkPath = False
        self.requestWaitingPoint = False
        self.waitingPoint = None
        self.queueToWaitingPoint = False
        self.approaching = False
        self.breakingDistance = 0
        self.maxBreakingDistance = ((self.maxSPD)**2) / (2*self.accel)
        self.resolvingConflicts = False
        self.ConflictAdvisory = False
        self.conflictList = []
        self.resolvingList = []
        self.retardPointCheck = False
        self.stopPoint = None
        self.requireLogTask = False
        self.orientation = 'N'
        self.compass = ['N','E','S','W']
        self.turnCounter = 0
        self.rotationProgress = 0
        self.isRotating = False
        
    def isIdle(self):
        return self.status == AGVStatus.IDLE
    
    def isTransit(self):
        return self.status == AGVStatus.TRANSIT
    
    def toTaskReceived(self):
        self.status = AGVStatus.TASKRECEIVED
    
    def initTask(self):
        # self.start = self.task.start
        self.dest = self.task.start
        
    def updateRemainingDistance(self, dest=None):
        if dest:
            path = [self.currentPos, dest]
            self.remainingDistance = self.mapper.getRemainingDistance(self.currentCoord, path)
        else:
            self.remainingDistance = self.mapper.getRemainingDistance(self.currentCoord, self.path)
    
    def setCrashed(self):
        self.speed = 0
        self.status = AGVStatus.CRASHED
        self.path = [self.currentPos]
        self.checkPath = False
        
    def transit(self, target=None):
        if target is None:
            target = self.initPoint
        print(f"AGV {self.ID}: Transit mode to point: {target}")
        self.dest = target
        self.status = AGVStatus.TRANSIT
        
    def transitToWaitingPoint(self, target, correction=False):
        if correction:
            print(f"AGV {self.ID}: Transferring to waiting point: {target}")
        self.dest = target
        self.waitingPoint = target
        self.requestWaitingPoint = False
    
    def step(self,sampleTime):
        # Finite-state machine
        self.statusID = self.status.value
        
        if self.status == AGVStatus.CRASHED:
            # nothing you can do when it's crashed, for now
            pass
        elif self.task is not None and self.status == AGVStatus.TASKRECEIVED:
            print(f"AGV {self.ID}: Task assigned task info {self.task.info()}")
            
            self.initTask()
            self.task.toAssigned()
            self.requireLogTask = True
            self.status = AGVStatus.PROCESSING
            self.pathRequest = True
            print("AGV {}: Task Initialized".format(self.ID))
            
        elif self.status == AGVStatus.PROCESSING:
            if not self.path or len(self.path) == 1:
                print(f"AGV {self.ID}: Processing task Pickup: {self.task.start} Dropoff: {self.task.dest}")
                self.dest = self.task.start
                self.pathRequest = True
                self.requestWaitingPoint = True
            elif self.path:
                print("AGV {}: Path to pickup is created => [{}] {} ".format(self.ID, len(self.getPath())-1, self.path))
                self.pathRequest = False
                self.checkPath = True
                self.start = self.task.start
                self.status = AGVStatus.PICKINGUP
                
        elif self.status == AGVStatus.PICKINGUP:
            if not self.path or len(self.path) == 1:
                self.pathRequest = True
            else:
                if self.isApproaching():
                    self.stopPoint  = None
                    self.retard = False
                    if self.proceed(self.task.start, sampleTime):
                        if self.currentPos == self.task.start:
                            print(f"AGV {self.ID}: Arrive pick-up point {self.task.start}")
                            self.task.toProcessing()
                            self.requireLogTask = True
                            self.nextPoint = None 
                            self.path.clear()
                            self.queueToWaitingPoint = False
                            self.retardRequest = False
                            self.waitingPoint = None
                            self.requestWaitingPoint = True
                            self.approaching = False
                            self.dest = self.task.dest
                            self.status = AGVStatus.TRANSFERRING 
                
                elif self.currentPos == self.waitingPoint and not self.isQueuing():
                    print(f"AGV {self.ID}: Arrive waiting point {self.waitingPoint}")
                    self.queueToWaitingPoint = True
                    self.pathRequest = True
                    self.retardRequest = True
                    self.dest = self.task.start
                elif self.proceed(self.dest, sampleTime):
                    if self.currentPos == self.waitingPoint:
                        if not self.isQueuing():
                            print(f"AGV {self.ID}: Arrive waiting point {self.waitingPoint}")
                        self.queueToWaitingPoint = True
                        self.pathRequest = True
                        self.retardRequest = True
                        self.dest = self.task.start
                        self.stopPoint  = None
                    elif self.currentPos == self.task.start: 
                        print(f"AGV {self.ID}: Arrive pick-up point {self.task.start}")
                        self.task.toProcessing()
                        self.requireLogTask = True
                        self.nextPoint = None 
                        self.path.clear()
                        self.queueToWaitingPoint = False
                        self.retardRequest = False
                        self.waitingPoint = None
                        self.requestWaitingPoint = True
                        self.approaching = False
                        self.dest = self.task.dest
                        self.status = AGVStatus.TRANSFERRING
                
        elif self.status == AGVStatus.TRANSFERRING:
            if not self.path:
                self.pathRequest = True
            elif self.path and self.pathRequest:
                print("AGV {}: Path to destination is created => [{}] {}".format(self.ID, len(self.getPath())-1, self.path))
                self.nextPoint = self.path[1] #second point
                self.updateRemainingDistance()
                self.pathRequest = False
                self.checkPath = True
            elif self.currentPos == self.task.dest:
                print("AGV {}: Task is delivered".format(self.ID))
                self.task.toCompleted()
                self.requireLogTask = True
                self.nextPoint = None 
                self.path.clear()
                self.status = AGVStatus.IDLE
            else:
                if self.isApproaching():
                    self.stopPoint  = None
                    self.retard = False
                    if self.proceed(self.task.dest, sampleTime):
                        if self.currentPos == self.task.dest:
                            print("AGV {}: Task is delivered".format(self.ID))
                            self.task.toCompleted()
                            self.requireLogTask = True
                            self.nextPoint = None 
                            self.path.clear()
                            self.queueToWaitingPoint = False
                            self.retardRequest = False
                            self.requestWaitingPoint = False
                            self.approaching = False
                            self.waitingPoint = None
                            self.status = AGVStatus.IDLE
                elif self.proceed(self.dest, sampleTime):
                    if self.currentPos == self.waitingPoint:
                        self.stopPoint  = None
                        if not self.queueToWaitingPoint:
                            print(f"AGV {self.ID}: Arrive waiting point {self.waitingPoint}")
                        self.queueToWaitingPoint = True
                        self.pathRequest = True
                        self.retardRequest = True
                        self.dest = self.task.dest
                
        elif self.status == AGVStatus.TRANSIT:
            if self.currentPos == self.dest:
                print(f"AGV {self.ID}: Arrives idle point {self.dest}")
                self.status = AGVStatus.IDLE
            elif not self.path or len(self.path) == 1:
                print(f"AGV {self.ID}: requesting path to idle point {self.dest}")
                self.pathRequest = True
            elif self.path and self.pathRequest:
                print("AGV {}: Path to idle point is created => [{}] {} ".format(self.ID, len(self.getPath())-1, self.path))
                self.pathRequest = False
                self.checkPath = True
            elif self.proceed(self.dest, sampleTime): 
                self.nextPoint = None 
                self.path = [self.path[-1]]
                print(f"AGV {self.ID}: Arrives idle point {self.dest}")
                self.status = AGVStatus.IDLE
            
            
            
    def proceed(self, target, sampleTime):
        if not self.path :
            self.nextPoint = self.currentPos
        elif len(self.getPath()) == 1:
            self.nextPoint = self.currentPos
        else:
            self.nextPoint = self.path[1]
        nextPointCoord = self.mapper.pointConvertCoord(self.nextPoint)
        targetCoord = self.mapper.pointConvertCoord(target)
        # print("AGV", self.ID,"self.currentPos", self.currentPos, "currentCoord", self.currentCoord, "Next Point", self.nextPoint, "Remaining Distance", self.remainingDistance, "speed", self.speed)
        
        self.direction = nextPointCoord - self.currentCoord
        
        # check orientation
        if self.direction[0] > 0:
            self.pathOrientation = 'E'
        elif self.direction[0] < 0:
            self.pathOrientation = 'W'
        elif self.direction[1] > 0:
            self.pathOrientation = 'N'
        else:
            self.pathOrientation = 'S'
        
        if self.compass.index(self.orientation) - self.compass.index(self.pathOrientation) == 0:
            print('Right direction! No need change')
        elif self.compass.index(self.orientation) - self.compass.index(self.pathOrientation) == -1 or self.compass.index(self.orientation) - self.compass.index(self.pathOrientation) == 3:
            print('90 deg right turn!', self.turnCounter, self.rotationProgress)
            self.turnCounter += self.sampleTime
            self.rotationProgress = self.rotateSPD
            self.isRotating = True
        elif self.compass.index(self.orientation) - self.compass.index(self.pathOrientation) == 1  or self.compass.index(self.orientation) - self.compass.index(self.pathOrientation) == -3:
            print('90 deg left turn!')
            self.turnCounter += self.sampleTime
            self.rotationProgress = self.rotateSPD
            self.isRotating = True
        elif abs(self.compass.index(self.orientation) - self.compass.index(self.pathOrientation)) == 2:
            print('180 deg turn!')
            self.turnCounter += self.sampleTime
            self.rotationProgress = self.rotateSPD * 2
            self.isRotating = True
        
        if self.isRotating:
            if self.turnCounter >= self.rotationProgress :
                print('Rotation completed!')
                self.turnCounter = 0
                self.rotationProgress = 0
                self.orientation = self.pathOrientation
                self.isRotating = False
            else:
                return False
        
        v = sqrt(self.direction[0]**2 + self.direction[1]**2)
        # print("self.direction: {} v:{}".format(self.direction, v))
        if self.isApproaching():
            self.retardRequest = False
        if v != 0: 
            u = self.direction / v
            if self.retardRequest:
                if self.speed != 0:
                    if self.stopPoint is not None:
                        self.retardPointCheck = True
                    else:
                        self.retardPointCheck = False
                    
                    if not self.retardPointCheck:
                        remainingPointIndex = ceil(self.breakingDistance / self.mapper.length)
                        if not self.stopPoint:
                            self.stopPoint = self.path[remainingPointIndex]
                        self.retardPointCheck = True
                    
                    if self.stopPoint not in self.path:
                        remainingPointIndex = ceil(self.breakingDistance / self.mapper.length)
                        self.stopPoint = self.path[remainingPointIndex]
                        self.retardPointCheck = True
                    
                    self.remainingDistanceToStopPoint = self.mapper.getRemainingDistance(self.currentCoord, self.path[:self.path.index(self.stopPoint)+1])
                        
                    if self.remainingDistanceToStopPoint <= self.breakingDistance or self.stopPoint is None:
                        if self.speed >= 0 and self.speed <= self.maxSPD:
                            self.speed -= self.accel*sampleTime
                        if round(self.speed,3) < 1e-3: self.speed = 0
                    # DEBUG: not the right way to do, it's a case of instant start/stop
                    else:
                        movement = u * self.speed * sampleTime
                        if sqrt((movement[0])**2 + (movement[1])**2) > self.remainingDistanceToStopPoint:
                            self.currentPos == self.stopPoint
                            self.speed = 0
                            self.currentCoord = self.mapper.pointConvertCoord(self.currentPos)
                    if self.currentPos == self.stopPoint:
                        self.speed = 0
                        self.currentCoord = self.mapper.pointConvertCoord(self.currentPos)
                if self.speed == 0:
                    self.currentCoord = self.mapper.pointConvertCoord(self.currentPos)
                    self.stopPoint = self.currentPos
            elif self.retard:
                if self.speed >= 0 and self.speed <= self.maxSPD:
                    self.speed -= self.accel*sampleTime
                if round(self.speed,3) < 1e-3: self.speed = 0
            else:
                if self.speed < self.maxSPD:
                    self.speed += self.accel*sampleTime
                if self.speed > self.maxSPD: self.speed = self.maxSPD
                if self.retardPointCheck:
                    self.retardPointCheck = False
                if self.stopPoint:
                    self.stopPoint = None
            
            self.speed = round(self.speed, 3)
            movement = u * self.speed * sampleTime
            self.currentCoord = self.currentCoord + movement
        
        
        # TODO: Not sure if it's the best way to do this
        if (abs(self.currentCoord - nextPointCoord) <= self.speed*sampleTime).all():
            self.currentPos = self.nextPoint
            self.currentCoord = nextPointCoord
            self.checkPath = True
            if self.path:
                del self.path[0]
                if not self.path:
                    self.path = [self.currentPos]
        if self.queueToWaitingPoint:
            self.updateRemainingDistance(dest = self.dest)
        else:
            self.updateRemainingDistance()
            
        self.breakingDistance = ((self.speed)**2) / (2*self.accel)  # v^2 = u^2 + 2as => v=0 => s = (-u^2)/(2a)
        if self.remainingDistance <= self.breakingDistance*1.15:
            self.retard = True
        else:
            self.retard = False
            
        if self.currentPos == target and (self.currentCoord == targetCoord).all():
            self.speed = 0
            return True
        elif self.currentPos == self.path[-1] and self.segmentPath:
            self.speed = 0
            self.path = self.segmentPath.pop(0)
        
        return False
    
    def turnOffRetard(self):
        self.retardRequest = False
    
    def turnOnRetard(self):
        self.retardRequest = True
    
    def isRetarding(self):
        return self.retardRequest
    
    def getBreakingDistance(self):
        return self.breakingDistance
    
    def hasTask(self):
        return self.task != None
    
    def getCurrentPosandDest(self):
        return self.currentPos, self.dest
    
    def getTaskStartDest(self):
        return self.task.start, self.task.dest
    
    def getCurrentPos(self):
        return self.currentPos
    
    def hasArrived(self):
        return self.currentPos == self.dest
    
    def assignPath(self, path, segmentPath):
        self.fullpath = path
        self.segmentPath = segmentPath
        self.path = self.segmentPath.pop(0)
        self.pathRequest = False
    
    def isRequestingPath(self):
        return self.pathRequest
    
    def isRequestingPath(self):
        return self.pathRequest
    
    def isRequestingWaitingPoint(self):
        return self.requestWaitingPoint 
    
    def isQueuing(self):
        return self.queueToWaitingPoint
    
    def isApproaching(self):
        return self.approaching
    
    def approachEndPoint(self):
        self.approaching = True
    
    def getStatus(self):
        return self.status
    
    def isCrashed(self):
        return self.status==AGVStatus.CRASHED
    
    def isProcessing(self):
        return self.status==AGVStatus.PROCESSING
    
    def isTransferring(self):
        return self.status==AGVStatus.TRANSFERRING
    
    def isPickingUp(self):
        return self.status==AGVStatus.PICKINGUP
    
    def requirePathCheck(self):
        return self.checkPath
    
    def getWaitingPoint(self):
        return self.waitingPoint
    
    def donePathCheck(self):
        self.checkPath = False
    
    def getCurrentCoord(self):
        return self.currentCoord
    
    def getRemainingDistance(self):
        return self.remainingDistance
    
    def getPath(self):
        if type(self.path) == int:
            return list([self.path])
        return self.path.copy()
    
    def getSpeed(self):
        return self.speed
    
    def isStopped(self):
        return self.speed == 0
    
    def getNextPoint(self):
        if len(self.getPath()) > 1:
            return self.path[1]
        return None
    
    def isResolvingConflicts(self):
        return self.resolvingConflicts
    
    def hasConflictAdvisory(self):
        return self.conflictsAdvisory
    
    def addConflict(self, agvID):
        if type(agvID) == list:
            for id in agvID:
                if id not in self.conflictList and id != self.ID:
                    self.conflictList.append(id)
            self.ConflictAdvisory = True
            return
        
        if agvID not in self.conflictList:
            self.conflictList.append(agvID)
        self.ConflictAdvisory = True
        self.retardRequest = True
    
    def removeConflict(self, agvID):
        if agvID in self.conflictList:
            self.conflictList.remove(agvID)
        if agvID in self.resolvingList:
            self.resolvingList.remove(agvID)
                
        if not self.conflictList:
            self.ConflictAdvisory = False
            self.resolvingConflicts = False
            self.retardRequest = False
            
    def addResolvingList(self, agvID):
        if agvID not in self.resolvingList:
            self.resolvingList.append(agvID)
        self.resolvingConflicts = True
        
    def removeResolveList(self, agvList):
        for agvID in agvList:
            if agvID in self.resolvingList:
                self.resolvingList.remove(agvID)
    
    def removeResolveList(self):
        self.resolvingList.clear()
        
    def removeConflictList(self):
        self.conflictList.clear()
    
    
    def getConflictList(self):
        return self.conflictList
    
    def getResolvingList(self):
        return self.resolvingList
    
    def assignStopPoint(self, stopPoint, forced=False):
        if forced:
            self.stopPoint = stopPoint
            return
        
        if self.stopPoint is None:
            self.stopPoint = stopPoint
        elif stopPoint is None:
            return
        elif self.stopPoint not in self.path:
            self.stopPoint = stopPoint
        elif self.path.index(stopPoint) < self.path.index(self.stopPoint):
            self.stopPoint = stopPoint
        
    
    def getStopPoint(self):
        return self.stopPoint
    
    def isRequiringLogTask(self):
        return self.requireLogTask
    
    def comepleteLogTime(self):
        self.requireLogTask = False
    
    def clearTask(self):
        self.task = None
from enum import Enum

class TaskStatus(Enum):
    PENDING = 0
    ASSIGNED = 1
    PROCESSING = 2
    COMPLETED = 3
    
class Task:
    def __init__(self, ID, start, dest, initTime, pickupNo=None, dropoffNo=None):
        self.taskID = ID
        self.status = TaskStatus.PENDING
        self.start = start
        self.dest = dest
        self.initTime = initTime
        self.assignedAGV = None
        self.pickupNo = pickupNo
        self.dropoffNo = dropoffNo
        self.timelog = {
            "initTime": initTime,
            "assignTime": None,
            "pickupTime": None,
            "comepleteTime": None,
        }
        requireLogTime = False
    
    def getStatus(self):
        return self.status
    
    def toAssigned(self):
        self.status = TaskStatus.ASSIGNED
    
    def toProcessing(self):
        self.status = TaskStatus.PROCESSING
    
    def toCompleted(self):
        self.status = TaskStatus.COMPLETED
    
    def isDelivered(self):
        return self.status == TaskStatus.COMPLETED
    
    def info(self):
        print(f"taskID: {self.taskID} start: {self.start} dest: {self.dest} pickupNo:{self.pickupNo} dropoffNo:{self.dropoffNo} initTime:{self.initTime}")
    
    def getInitTime(self):
        return self.initTime
    
    def getPickupPoint(self):
        return self.start
    
    def logTime(self, logTime):
        for key, value in self.timelog.items():
            if value is None:
                self.timelog[key] = logTime
                break
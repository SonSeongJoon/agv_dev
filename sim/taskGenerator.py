from task import Task
from random import choice, randint

class TaskGenerator:
    def __init__(self, mapPoints, fixedPickUpPoint, fixedDropOffPoint, orderPickUpPoint ,orderDropOffPoint):
        self.mapPoints = mapPoints
        self.fixedPickUpPoint = fixedPickUpPoint
        self.fixedDropOffPoint = fixedDropOffPoint
        self.orderPickUpPoint = orderPickUpPoint
        self.orderDropOffPoint = orderDropOffPoint
        
        self.PickUpPointChoice = fixedPickUpPoint
        self.DropOffPointChoice = fixedDropOffPoint
        self.idCounter = 0
        
    def generateSimpleTask(self, start, dest, initTime):
        newTask = Task(ID=self.idCounter, start=start, dest=dest, initTime=initTime)
        self.idCounter += 1
        return newTask
    
    def generateRandomTask(self, initTime, duplicate = True):
        if not duplicate:
            start = choice(self.fixedPickUpPoint)
            dest = choice(self.fixedDropOffPoint)
        else:
            if not self.PickUpPointChoice:
                self.PickUpPointChoice = self.fixedPickUpPoint
            else:
                start = choice(self.PickUpPointChoice)
                self.PickUpPointChoice.delete(start)
                
            if not self.DropOffPointChoice:
                self.DropOffPointChoice = self.fixedDropOffPoint
            else:
                start = choice(self.DropOffPointChoice)
                self.DropOffPointChoice.delete(start)
        
        newTask = Task(ID=self.idCounter, start=start, dest=dest, initTime=initTime)
        self.idCounter += 1
        
        return newTask
    
    def generateTask(self, orderPickup, orderDropoff, initTime):
        start = self.fixedPickUpPoint[self.orderPickUpPoint.index(orderPickup)]
        dest = self.fixedDropOffPoint[self.orderDropOffPoint.index(orderDropoff)]
        newTask = Task(ID=self.idCounter, start=start, dest=dest, initTime=initTime, pickupNo=int(orderPickup), dropoffNo=int(orderDropoff))
        self.idCounter += 1
        return newTask
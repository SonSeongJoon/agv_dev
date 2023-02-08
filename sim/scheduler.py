class Scheduler:
    def __init__(self):
        self.taskList = []
        self.availableTaskList = []
        self.totalNumberOfTask = 0

    def addTask(self, task):
        self.taskList.append(task)
        self.totalNumberOfTask += 1
    
    def update(self, timestep):
        if self.taskList:
            while len(self.taskList) > 0:
                task = self.taskList[0]
                if task.getInitTime() < timestep:
                    self.availableTaskList.append(task)
                    self.taskList.pop(0)
                else:
                    break
    
    def getRemainingTasks(self):
        return len(self.taskList) + len(self.availableTaskList)
    
    def getTask(self):
        '''
        # **Scheduling algorithm insert here**
        currently it uses GREEDY algorithm, return whatever the first task
        '''
        if self.availableTaskList:
            return self.availableTaskList.pop(0)
        else:
            return None
    
    def getFirstTaskPickUpLocation(self):
        return self.availableTaskList[0].getPickupPoint()
    
    def returnTask(self,task):
        self.availableTaskList.insert(0, task)
        
    def isEmpty(self):
        # print('taskList', self.taskList)
        return not bool(self.availableTaskList)
    
    def finishedAllTasks(self):
        return not bool(self.taskList)
    
    def showAvailableTask(self):
        return self.availableTaskList
    
    def showNextTask(self):
        if self.taskList:
            print('Next task')
            self.taskList[0].info()
        else:
            print('No next task')
    
    def getNextTaskTime(self):
        if self.taskList:
            return self.taskList[0].getInitTime()
        else:
            return None
        
    def getTotalNumberOfTasks(self):
        return self.totalNumberOfTask
class Dispatcher():
    def __init__(self, mapper):
        self.mapper = mapper
    
    def findIdleAGV(self,  fleet, method='GREEDY', taskLocation=None):
        '''
        # **dispatch algorithm insert here**
        defult it uses GREEDY. return whatever the first idle agv
        
        available method:
        - GREEDY
        - shortestDistance
        '''
        if method=='GREEDY':
            for agv in fleet:
                if agv.isIdle() or agv.isTransit():
                    return agv.ID
            return None
        
        if method=='shortestDistance':
            distanceList = {}
            
            if taskLocation is None:
                raise ValueError('taskLocation is not a valid task location')
            
            for agv in fleet:
                if agv.isIdle() or agv.isTransit():
                    agvCoord = agv.getCurrentCoord()
                    distanceList[agv.ID] = (agvCoord[0]-taskLocation[0])**2 + (agvCoord[1]-taskLocation[1])**2  
            if not distanceList:
                return None
            
            distanceList = {k: v for k, v in sorted(distanceList.items(), key=lambda item: item[1])}
            # print(distanceList)
            return next(iter(distanceList))
    
    def hasIdleAGV(self, fleet):
        for agv in fleet:
            if agv.isIdle() or agv.isTransit():
                return True
        return False
    
    def assignTask(self, id, task, fleet):
        fleet[id].task = task
        fleet[id].toTaskReceived()

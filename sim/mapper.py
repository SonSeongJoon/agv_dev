import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from math import sqrt, ceil
from random import sample

class Mapper:
    def __init__(self, width, height, length):
        self.G = None
        self.pos=None
        self.width = width
        self.height = height
        self.length = length
        self.numPoints = None
        
    def initSquareMap(self, numNode):
        self.G = nx.Graph()
        row = 0
        totalNode = numNode ** 2
        
        for i in range(totalNode):
            if i % numNode == 0:
                row += 1
            self.G.add_node(i, pos=(i % numNode, row))
        
        for i in range(totalNode-1):
            if i % numNode != numNode - 1:
                self.G.add_edge(i, i+1)
                if (i+numNode) < (totalNode-1):
                    self.G.add_edge(i, i+numNode)
            else:
                if (i+numNode) <= (totalNode-1):
                    self.G.add_edge(i, i+numNode)
            self.G.add_nodes_from([2, 3])
            
        self.getPos()
        self.numPoints = len(self.pos)
        
        return self.G
    
    def initRectagnleMap(self, width, height, length):
        self.G = nx.Graph()
        row = 0
        totalNode = width * height
        
        self.width = width
        self.height = height
        self.length = length
        
        for i in range(totalNode):
            if i % width == 0 and i!=0:
                row += length
            self.G.add_node(i, pos=((i % width)*length, row))
        
        for i in range(totalNode-1):
            if i % width != width - 1:
                self.G.add_edge(i, i+1)
                if (i+width) < (totalNode-1):
                    self.G.add_edge(i, i+width)
            elif (i+width) <= (totalNode-1):
                    self.G.add_edge(i, i+width)
            self.G.add_nodes_from([2, 3])
        
        self.getPos()
        self.numPoints = len(self.pos)
        
        return self.G
    
    def initDirectedRectagnleMap(self, width, height, length):
        self.G = nx.DiGraph()
        rowY = 0
        totalNode = width * height
        
        self.width = width
        self.height = height
        self.length = length
        
        for i in range(totalNode):
            if i % width == 0 and i!=0:
                rowY += length
            self.G.add_node(i, pos=((i % width)*length, rowY))
        
        rowNumber=0
        colNumber=0
        for i in range(totalNode-1):
            # row
            if (i+1) % width == 0 and i != 0:
                rowNumber +=1
                continue
            
            if rowNumber % 2 == 0:
                self.G.add_edge(i+1, i)
            else:
                self.G.add_edge(i, i+1)
            
        for i in range(width):
            if colNumber % 2 == 0:
                markerPoint = i
                for _ in range(height-1):
                    self.G.add_edge(markerPoint, markerPoint+width)
                    markerPoint += width
            else:
                markerPoint = i + height*width - width
                for _ in range(height):
                    if (markerPoint-width) < 0:
                        continue
                    self.G.add_edge(markerPoint, markerPoint-width)
                    markerPoint -= width
            
            colNumber +=1
        
        self.getPos()
        self.numPoints = len(self.pos)
        
        return self.G
    
    def initCircleDirectedRectagnleMap(self, width, height, length, margin=3):
        self.G = nx.DiGraph()
        rowY = 0
        totalNode = width * height
        
        self.width = width
        self.height = height
        self.length = length
        
        for i in range(totalNode):
            if i % width == 0 and i!=0:
                rowY += length
            self.G.add_node(i, pos=((i % width)*length, rowY))
        
        rowNumber=0
        colNumber=0
        for i in range(totalNode-1):
            # row
            if (i+1) % width == 0 and i != 0:
                rowNumber +=1
                continue
            
            if rowNumber % 2 == 0:
                if rowNumber == 0:
                    if i % 2 ==0:
                        self.G.add_edge(i+1, i)
                elif rowNumber <= margin or rowNumber >= (height - margin -1):
                    pass
                else:
                    self.G.add_edge(i+1, i)
            else:
                if rowNumber == height-1:
                    if i % 2 == 0:
                        self.G.add_edge(i, i+1)
                elif rowNumber <= margin or rowNumber >= (height -margin):
                    pass
                else:
                    self.G.add_edge(i, i+1)
        
        for i in range(width):
            # column
            if colNumber % 2 == 0:
                markerPoint = i
                for j in range(height-1):
                    if i == 0:
                        if margin < j <  (height-margin - 2):
                            if j % 2 == 0:
                                self.G.add_edge(markerPoint, markerPoint+width)
                        else:
                            self.G.add_edge(markerPoint, markerPoint+width)
                    else:
                        self.G.add_edge(markerPoint, markerPoint+width)
                    markerPoint += width
            else:
                markerPoint = i + height*width - width
                for j in range(height):
                    if (markerPoint-width) < 0:
                        continue
                    if i == width -1:
                        if margin < j <  (height-margin-2):
                            if j % 2 == 0:
                                self.G.add_edge(markerPoint, markerPoint-width)
                        else:
                            self.G.add_edge(markerPoint, markerPoint-width)
                    else:
                        self.G.add_edge(markerPoint, markerPoint-width)
                    markerPoint -= width
            
            colNumber +=1
        
        self.getPos()
        self.numPoints = len(self.pos)
        
        return self.G
    
    def getNumberofPoints(self):
        return self.numPoints
    
    def listPos(self):
        print(self.pos)
    
    def draw(self, show=False):
        nx.draw(self.G, with_labels=True, pos=self.pos, node_size=100, node_color='w',font_size=8, arrows=None)
        if show:
            plt.show()
    
    def drawGrid(self, show=False):
        nx.draw(self.G, with_labels=False, pos=self.pos, node_size=0, arrows=None)
        if show:
            plt.show()
    
    def shortestPath(self, start, dest):
        return nx.shortest_path(self.G, start, dest)
    
    def allShortestPath(self, start, dest):
        return list(nx.all_shortest_paths(self.G, start, dest))
    
    def drawPath(self, path, color):
        path_edges = zip(path,path[1:])
        path_edges = set(path_edges)
        # nx.draw_networkx_nodes(self.G,self.pos,nodelist=path,node_color=color)
        nx.draw_networkx_edges(self.G,self.pos,edgelist=path_edges,edge_color=color,width=5)
    
    def getPos(self):
        self.pos = nx.get_node_attributes(self.G,'pos')
        return self.pos
    
    def getMap(self):
        return self.G
    
    def pathConvertCoordPath(self, path):
        for i in range(len(path)):
            path[i] = np.asarray(self.pos[i])
        return path
    
    def pointConvertCoord(self, point):
        return np.asarray(self.pos[point])
    
    def hasArrived(self, pt1, pt2, spd, dt):
        return (abs(pt1-pt2) <= spd*dt).all()
    
    def getLastPoint(self):
        return self.pos[len(self.pos)-1]
    
    def getRemainingDistance(self, pos, path):
        if len(path) == 1:
            return 0
        
        if len(path) == 2:
            nextPointCoord = self.pointConvertCoord(path[1])
            return sqrt((pos[0]-nextPointCoord[0])**2+(pos[1]-nextPointCoord[1])**2)
        
        nextPointCoord = self.pointConvertCoord(path[1])
        d1 = sqrt((pos[0]-nextPointCoord[0])**2+(pos[1]-nextPointCoord[1])**2) 
        d2 = (len(path) - 2) * self.length
        # print(f"path {path} pos {pos} path {path} d1 {d1} d2 {d2} distance {d1+d2}")
        return d1+d2
    
    def generateRandomPoints(self, num):
        return sample(range(self.numPoints), num)
        
    def initHorizontal(self, numberOfAGV):
        interval = ceil(self.width / numberOfAGV)
        y = round(self.height/2)
        firstPoint = y * self.width
        return list(firstPoint + (i*interval) for i in range(numberOfAGV))
    
    
    
    def convertPickupPoint(self, orderPickUpPoint):
        self.orderPickUpPoint = orderPickUpPoint
        if len(orderPickUpPoint) > (self.width / 2):
            raise ValueError("The width of map cannot contain all the pickup points")
        
        topRow = np.array(list(range(self.width * (self.height - 1) -1, self.width * self.height-1)))
        midpoint = int(self.width / 2)
        numberOfHalfPickupPoints = int(len(orderPickUpPoint) / 2)
        startPos = midpoint - (numberOfHalfPickupPoints * 2)
        
        numberOfHalfPickupPoints = np.array(list(startPos + x *2 for x in range(len(orderPickUpPoint))))
        # fixedDropOffPoint = topRow[numberOfHalfPickupPoints].tolist()
        
        return topRow[numberOfHalfPickupPoints].tolist()

    def convertDropoffPoint(self, orderDropOffPoint):
        specialPoints=[]
        self.orderDropOffPoint = orderDropOffPoint
        
        for pt in orderDropOffPoint.copy():
            if pt >= 1000:
                specialPoints.append(orderDropOffPoint.pop(orderDropOffPoint.index(pt)))
        midpoint = int(self.width / 2)
        numberOfHalfDropoffPoints = int(len(orderDropOffPoint) / 2)
        startPos = midpoint - (numberOfHalfDropoffPoints * 2)
        
        
        fixedDropOffPoint = list(startPos + x *2 for x in range( len(orderDropOffPoint)))
        
        manualPoint=[]
        if specialPoints:
            rightestCol = list((self.width * x -1)  for x in range(1, self.height))
            for i in range(len(specialPoints)):
                fixedDropOffPoint.append(rightestCol[5+2*i])
                manualPoint.append(rightestCol[5+2*i])
        
        return fixedDropOffPoint, manualPoint
    
if __name__ == '__main__':
    height=10
    width=20
    gridSize=0.25
    
    map = Mapper(width=width,height=height,length=gridSize)
    map.initRectagnleMap(width=width,height=height,length=gridSize)
    fig, ax = plt.subplots()
    ax.set_xlim((-gridSize, width*gridSize))
    ax.set_ylim((-gridSize, height*gridSize))
    ax.set_aspect('equal', anchor='C')
    plt.tight_layout()
    
    start, dest = 1, 150
    path = map.shortestPath(start, dest)
    print(f'shortest distance is {(len(path)-1)*gridSize},  {path}')
    
    map.drawPath(path, 'r')
    
    # map.draw()
    map.drawGrid()
    
    plt.show()

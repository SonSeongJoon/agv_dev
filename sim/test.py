from fms import FMS
from mapper import Mapper
from taskGenerator import TaskGenerator
from logger import Logger
from fms import FMS
import random
import configparser
import json
from memory_profiler import profile
import networkx as nx
import time

def run():
    random.seed(5)
    
    mapper = Mapper()
    G = mapper.initRectagnleMap(5, 5, .25)
    
    print(len(G.edges))
    
    G.add_edge(1, 2, weight=3)
    
    print(G[1][2])
    print(G.edges)
    print(len(G.edges))
    
    G.add_edge(3, 2, weight=999)
    # G.add_edge(3, 13, weight=999)
    start = 3
    end = 8
    
    r = G.edges(8)
    
    for pts in r:
        G.add_edge(pts[0], pts[1], weight=999)
    # G.add_edge(9, 8, weight=999)
    # print(G[3][2])
    
    p = nx.shortest_path(G, 3, 5,weight='weight')
    print(p)
    
    
    # mapper.draw(True)

def test():
    start = time.perf_counter()
    for i in range(10000):
        print(i)
    print(time.perf_counter() - start)
    
def sortPath():
    path = [50, 51, 52, 53, 54, 55, 56, 57, 58, 68, 78, 88, 98, 97, 96, 95, 85, 75]
    print(path)
    
    newPath = []
    segment = []
    while path:
        print('segment', segment)
        point = path.pop(0)
        print('point', point)
        if (not newPath and not segment) or (newPath and not segment) :
            segment = [point]
        elif len(segment) == 1:
            segment.append(point)
        else:
            # print('>>>', abs(segment[-1] - segment[-2]) == abs(point - segment[-1]))
            if abs(segment[-1] - segment[-2]) == abs(point - segment[-1]):
                segment.append(point)
            else:
                newPath.append(segment.copy())
                print('!!', segment)
                print('newPath', newPath)
                segment = [segment[-1], point]
    
    if segment:
        newPath.append(segment.copy())
    
    print('final', newPath)

sortPath()
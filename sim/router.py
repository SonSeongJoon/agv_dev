import networkx as nx

class Router():
    def __init__(self, mapper):
        self.mapper = mapper
        self.posList = None
    
    def shortestPath(self, start, dest):
        '''
        # **Routing algorithm insert here**
        The shortest path is made here, all customizable 
        currently it uses networkx shortest_path method, which uses dijkstra
        '''
        return nx.shortest_path(self.mapper.G, start, dest)
    
    def updatePosList(self, posList):
        self.posList = posList
    
    def shortestPathWithRestriction(self, restrictedPoint, start, dest, compulPoint=None):
        H = self.mapper.G.copy()
        for pos in self.posList:
            edges = H.edges(pos)
            # print("edges", edges)
            for edge in edges:
                # print(edge, "is restricted")
                H.add_edge(edge[0], edge[1], weight=50)
        
        for node in restrictedPoint:
            if (node - self.mapper.width) == compulPoint:
                continue
            H.remove_node(node)
        if compulPoint is not None:
            # H.add_edge(start, compulPoint, weight=0)
            try:
                H.remove_node(start)
                path = nx.dijkstra_path(H, int(compulPoint), int(dest))
                path.insert(0, start)
                return path
            except Exception as e:
                print('ERR (with compulpoint):', e)
                return None
            
        try:
            path = nx.dijkstra_path(H, int(start), int(dest))
            return path
        except Exception as e:
            print('ERR (without compulpoint):', e)
            return None
        
    def sortSegments(self, path):
        newPath = []
        segment = []
        print('original path', path)
        while path:
            point = path.pop(0)
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
                    segment = [segment[-1], point]
        
        if segment:
            newPath.append(segment.copy())
        
        # print(newPath)
        
        return newPath
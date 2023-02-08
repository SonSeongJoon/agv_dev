import pandas as pd
import numpy as np


class OrderProcessor:
    def __init__(self, csvFile):
        self.csvFile = csvFile
        self.df = pd.read_csv(csvFile, index_col=0)
    
    def getPickupPoint(self):
        return np.unique(self.df['pickup'].to_numpy()).tolist()
    
    def getDropoffPoint(self):
        return np.unique(self.df['dropoff'].to_numpy()).tolist()
    
    def processOrderData(self,sort=None, lite=True):
        if sort:
            self.df = self.df.sort_values(by=[sort])
            self.df = self.df.reset_index(drop=True)
            
        if lite:
            self.df = self.df.loc[:, 'time':'dropoff']
    
    def getOrderData(self):
        return self.df
        
    
    def filterManualProcess(self):
        self.df = self.df[self.df['dropoff']<=1000]
        self.df = self.df.reset_index(drop=True)
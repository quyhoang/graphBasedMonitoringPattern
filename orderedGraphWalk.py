# -*- coding: utf-8 -*-
"""
This works, but some pair of agents get stuck during simulation. Need to revise.
pattern1StrideCsvOutput
@author: leoes
This is to test new algorithm, compute coverage
"""

import csv

from mesa import Agent, Model
#from mesa.time import RandomActivation
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
from math import *
import numpy as np
import random

# =============================================================================
# with open('reportRandomStride.csv', 'a') as reportFile:
#     rewriter = csv.writer(reportFile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#     rewriter.writerow(['Step', 'InteractionRate', "AverageInteractionRate", 'Area', "CoveragePercentage", "AveragePercentage"]) 
#     
# =============================================================================

def compute_coverage(model):
    for agent in model.schedule.agents:
        model.coveredArea.append(agent.pos)
         
    coverIndex = len(set(model.coveredArea))
#    print("coverIndex", coverIndex)
    if coverIndex == 100:
        print(model.schedule.steps)
    return coverIndex


class MoniModel(Model):
    """A simple model of an economy where agents exchange currency at random.

    All the agents begin with one unit of currency, and each time step can give
    a unit of currency to another agent. Note how, over time, this produces a
    highly skewed distribution of wealth.
    """

    def __init__(self, N, width, height):
        self.num_agents = N
        self.width = width
        self.height = height
        self.grid = MultiGrid(height, width, False) #non toroidal grid
        self.schedule = SimultaneousActivation(self)
        self.datacollector = DataCollector(
            model_reporters={"Coverage": compute_coverage},
            agent_reporters={"Wealth": "wealth"}
        )
        # Create agents
        self.coveredArea = []
        self.interactionCount = 0
        self.interactionRateAverage = 0
        self.coveragePercentage = 0
        self.coveragePercentageAverage = 0
        
        #for ordered walk
        self.orientation = np.ones((self.height,self.width))
        self.orientation[:1] = np.full((1,self.width),2)
        self.orientation[:self.height,self.width-1:] = np.full((self.height,1),3)
        self.orientation[self.height-1:,] = np.full((1,self.width),4)
        self.orientation[:self.height,:1] = np.full((self.height,1),1)
        self.orientation[0][0] = 2
        
        
#        distribute the agents evently
        areaNum = ceil(sqrt(self.num_agents))
        areaDistx = self.width/(sqrt(self.num_agents))
        areaDistx = floor(areaDistx)
        areaDisty = self.height/(sqrt(self.num_agents))
        areaDisty = floor(areaDisty)
        
        self.dtx = areaDistx
        self.dty = areaDisty
        
        for i in range(self.num_agents):
            
            xlow = (i%areaNum)*areaDistx
            xup = xlow + areaDistx-1
            
            ylow = floor(i/areaNum)*areaDisty
            yup = ylow + areaDisty-1
        
            x = floor((xlow+xup)/2)+1
            y = floor((ylow+yup)/2)+1
            
           
            
            
            xlow = x-1
            xup = x+1
            ylow = y-1
            yup = y+1
            
#            create and add agent with id number i to the scheduler
            a = MoniAgent(i, self, xup, xlow, yup, ylow)
            self.schedule.add(a)
            
            #place agent at the center of its limit coor
            self.grid.place_agent(a, (x, y))
            # Add the agent to a random grid cell
            
#        this part is for visualization only
        self.running = True
        self.datacollector.collect(self)

    def step(self):
        self.interactionCount = 0
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)
        
       
        
        with open('reportRandomStride.csv', 'a') as reportFile:
            coverage = compute_coverage(self)
            percentage = ceil(10000*coverage/self.width/self.height)/100 
            
            interactionRate = self.interactionCount/self.num_agents/(self.num_agents-1)
            #number of interaction/possible interaction /2 for double counting
            interactionRate = ceil(10000*interactionRate)/100
            
            self.interactionRateAverage = (self.interactionRateAverage*(self.schedule.steps-1) + interactionRate)/self.schedule.steps
            self.interactionRateAverage  = ceil(100*self.interactionRateAverage)/100
            
            self.coveragePercentageAverage = (self.coveragePercentageAverage*(self.schedule.steps-1)+percentage)/self.schedule.steps
            self.coveragePercentageAverage = ceil(100*self.coveragePercentageAverage)/100
            
            rewriter = csv.writer(reportFile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            rewriter.writerow(["step:", self.schedule.steps, "InteractionRate:", interactionRate,'%', "AvgInteractionRate", self.interactionRateAverage,'%', "Coverage:", coverage, percentage,'%',self.coveragePercentageAverage,'%'])

#    def initPosTest(self)
    
   
    
    def run_model(self, n):
        for i in range(n):
#            self.initPos()
            self.step()
#            print(self.schedule.steps)
    
class MoniAgent(Agent):
    def __init__(self, unique_id, model, xup, xlow, yup, ylow):
#        , prevPos = (0,0)
        super().__init__(unique_id, model)
        self.xup = xup
        self.xlow = xlow
        self.yup = yup
        self.ylow = ylow
        self.wealth = 1
        self.returnFlag = False
        self.origin = ((xup-1),(yup-1)) #starting point
        self.forcex = 0
        self.forcey = 0
        self.nextPos = (0,0) 
		#new pos that will be move to in self.advance
		
        self.freeStep = 0 
        #number of steps with no close contact with other agents
        
        self.reflectX = True
        #plane of reflection parallel to x axis
        
        self.stepx = 0
        self.stepy = 0 
        #step in x and y direction of the last move
        

    
    
        
    def move(self):
        def new_pos():
#            xp, yp = self.prevPos
            x, y = self.pos
            
            orientation = self.model.orientation[x][y]+1
            if orientation > 4:
                orientation = 1
            if x == 0 and y == self.model.height-1:
                if orientation == 4 or orientation == 1:
                    orientation = 2
            elif x == 0 and y == 0:
                if orientation == 3 or orientation == 4:
                    orientation = 1
            elif x == self.model.width - 1 and y == 0:
                if orientation == 2 or orientation == 3:
                    orientation = 4
            elif x == self.model.width - 1 and y == self.model.height - 1:
                if orientation == 1 or orientation == 2:
                    orientation = 3
            elif y == self.model.height - 1:
                if orientation == 1:
                    orientation = 2
            elif y == 0:
                if orientation == 3:
                    orientation = 4
            elif x == 0:
                if orientation == 4:
                    orientation = 1
            elif x == self.model.width - 1:
                if orientation == 2:
                    orientation = 3
            
            self.model.orientation[x][y] = orientation
            
            
            if orientation == 1:
                new_pos = (self.pos[0],self.pos[1]+1)
            elif orientation == 2:
                new_pos = (self.pos[0] + 1,self.pos[1])
            elif orientation == 3:
                new_pos = (self.pos[0],self.pos[1]-1)
            elif orientation == 4:
                new_pos = (self.pos[0]-1,self.pos[1])
            
            return new_pos
            
        self.nextPos = new_pos()


    def step(self):
#        if self.returnFlag == False:
        self.move()
#        else:
#            self.returnn()
   
#    next step after staged change
    def advance(self):
        self.model.grid.move_agent(self, self.nextPos)
        


#visualization module =======================================================================
#============================================================================================
            
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5}

    if agent.wealth > 0:
        portrayal["Color"] = "green"
        portrayal["Layer"] = 0
    else:
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.5
    return portrayal


grid = CanvasGrid(agent_portrayal, 10, 10, 512, 512)
chart1 = ChartModule([{"Label": "Coverage", "Color": "#0000FF"}], data_collector_name='datacollector')


    
model_params = {
    "N": UserSettableParameter('slider', "Number of agents", 4, 2, 200, 1,
                               description="Choose how many agents to include in the model"),
    "width": 10, 
    "height": 10
}

#server = ModularServer(MoniModel, [grid, chart], "Money Model", model_params)
server = ModularServer(MoniModel, [grid, chart1], "Monitoring pattern", model_params)
server.port = 8426
server.launch()
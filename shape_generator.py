# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 16:43:39 2017

@author: Paweł Wojtkiewicz
"""

import math, random
from PIL import *


def clip(x, amin, amax) :
     if( amin > amax ) :  return x    
     elif( x < amin ) :  return amin
     elif( x > amax ) :  return amax
     else :             return x
     

def generatePolygon(aveRadius, irregularity, spikeyness, numVerts ) :
    irregularity = clip( irregularity, 0,1 ) * 2*math.pi / numVerts
    spikeyness = clip( spikeyness, 0,1 ) * aveRadius

    # generate n angle steps
    angleSteps = []
    lower = (2*math.pi / numVerts) - irregularity
    upper = (2*math.pi / numVerts) + irregularity
    sum = 0
    for i in range(numVerts) :
        tmp = random.uniform(lower, upper)
        angleSteps.append( tmp )
        sum = sum + tmp

    # normalize the steps so that point 0 and point n+1 are the same
    k = sum / (2*math.pi)
    for i in range(numVerts) :
        angleSteps[i] = angleSteps[i] / k

    # now generate the points
    points = []
    angle = random.uniform(0, 2*math.pi)
    for i in range(numVerts) :
        r_i = random.gauss(aveRadius, spikeyness) 
        while r_i>0.4 :
            r_i = random.gauss(aveRadius, spikeyness)
        x = 0.5 + r_i*math.cos(angle)
        y = 0.5 + r_i*math.sin(angle)
        points.append((x,y))

        angle = angle + angleSteps[i]

    return points


verts = generatePolygon(aveRadius=0.4, irregularity=0.2, spikeyness=0.2, numVerts=5 )


def generatePolygonShapePoints(verts,density):
    shape_points=[]
    
    for i in range(len(verts)):
    
        shape_points.append(verts[i])
    
        x1=verts[i][0]
        y2=verts[i][1]
    
        if i==max(range(len(verts))) :
            x1=verts[i][0]
            y1=verts[i][1]
            
            x2=verts[0][0]
            y2=verts[0][1]
        else:
            x1=verts[i][0]
            y1=verts[i][1]
            
            x2=verts[i+1][0]
            y2=verts[i+1][1]
        
        side_length=(((x1-x2)**2)+((y1-y2)**2))**(1/2)
        split_number=math.floor(side_length/density)
        
        if x1<x2:
            x_p=1
        else:
            x_p=-1
            
        if y1<y2:
            y_p=1
        else:
            y_p=-1    
        
        next_x=x1
        next_y=y1
        for j in range(split_number) :    
         next_x=next_x+(density*x_p)
         next_y=next_y+(density*y_p)
         next_point=[next_x,next_y]
         shape_points.append(next_point)
         
    return (shape_points)
         
            
sided_point_5 = generatePolygonShapePoints(verts,0.01)        
        

    
import matplotlib.pyplot as plt
plt.scatter([p[0] for p in verts], [p[1] for p in verts] )
plt.scatter([p[0] for p in sided_point_5], [p[1] for p in sided_point_5])

 





# -*- coding: utf-8 -*-
"""
Created on Sat Nov 18 16:43:39 2017

@author: Paweł Wojtkiewicz
v1.0
"""

import math, random, numpy
import json

def clip(x, amin, amax):
    if amin > amax:
        return x
    elif x < amin:
        return amin
    elif x > amax:
        return amax
    else:
        return x

def generatePolygon(aveRadius, irregularity, spikeyness, numVerts):
    irregularity = clip(irregularity, 0, 1) * 2 * math.pi / numVerts
    spikeyness = clip(spikeyness, 0, 1) * aveRadius

    # generate n angle steps
    angleSteps = []
    lower = (2 * math.pi / numVerts) - irregularity
    upper = (2 * math.pi / numVerts) + irregularity
    sum = 0
    for i in range(numVerts):
        tmp = random.uniform(lower, upper)
        angleSteps.append(tmp)
        sum = sum + tmp

    # normalize the steps so that point 0 and point n+1 are the same
    k = sum / (2 * math.pi)
    for i in range(numVerts):
        angleSteps[i] = angleSteps[i] / k

    # now generate the points
    points = []
    angle = random.uniform(0, 2 * math.pi)
    for i in range(numVerts):
        r_i = random.gauss(aveRadius, spikeyness)
        while r_i > 0.4:
            r_i = random.gauss(aveRadius, spikeyness)
        x = 0.5 + r_i * math.cos(angle)
        y = 0.5 + r_i * math.sin(angle)
        points.append((x, y))

        angle = angle + angleSteps[i]
        # Input test for verts outside scope.

    if((numpy.array(points) > 0.90).any() or (numpy.array(points) < 0.1).any()):
        print ("OUT OF SCOPE")
        return generatePolygon(aveRadius, irregularity, spikeyness, numVerts)

    return points


def generatePolygonShapePoints(verts, density):
    shape_points = []

    for i in range(len(verts)):

        shape_points.append(verts[i])
        # plt.scatter([p[0] for p in shape_points], [p[1] for p in shape_points])
        # plt.axis([0, 1, 0, 1])
        # plt.show()

        x1 = verts[i][0]
        y1 = verts[i][1]

        if i == (len(verts) - 1):
            x2 = verts[0][0]
            y2 = verts[0][1]
        else:
            x2 = verts[i + 1][0]
            y2 = verts[i + 1][1]

            #   print(x1, y1)
            #   print(x2, y2)

        side_length = (((x1 - x2) ** 2) + ((y1 - y2) ** 2)) ** (1 / 2)
        split_number = math.floor(side_length / density)
        if (split_number==0):
            continue

        next_x = x1
        next_y = y1

        x_delta = (x2 - x1) / split_number
        y_delta = (y2 - y1) / split_number
        for j in range(split_number):
            next_x = next_x + x_delta
            next_y = next_y + y_delta
            next_point = [next_x, next_y]
            shape_points.append(next_point)

    return shape_points


if __name__ == "__main__":
    shapes = []
    for _ in range(1):
        s = generatePolygon(aveRadius=0.6, irregularity=0.5, spikeyness=0.4, numVerts=7)
        shapes.append((s, s, False))
    #for _ in range(2):
    #    s = generatePolygon(aveRadius=0.6, irregularity=0.5, spikeyness=0.4, numVerts=7)
    #    shapes.append((s, s, True))
    #for _ in range(2):
    #     s1 = generatePolygon(aveRadius=0.6, irregularity=0.5, spikeyness=0.4, numVerts=7)
    #    s2 = generatePolygon(aveRadius=0.6, irregularity=0.5, spikeyness=0.4, numVerts=7)
    #    shapes.append((s1, s2, True))
    with open("shape_library.json", "w") as f:
        json.dump(shapes, f)

#TESTING
#verts = generatePolygon(aveRadius=0.3, irregularity=10, spikeyness=1000, numVerts=5)
#sided_point_5 = generatePolygonShapePoints(verts, 0.05)


#verts = generatePolygon(aveRadius=0.3, irregularity=0.5, spikeyness=0.4, numVerts=5)
#plt.scatter([p[0] for p in verts], [p[1] for p in verts], color='red')
#plt.axis([0, 1, 0, 1])
#plt.show()

#plt.scatter([p[0] for p in sided_point_5], [p[1] for p in sided_point_5])
#plt.scatter([p[0] for p in verts], [p[1] for p in verts], color='red')
#plt.axis([0, 1, 0, 1])
#plt.show()
#import matplotlib.pyplot as plt

#verts = generatePolygon(aveRadius=0.6, irregularity=0.5, spikeyness=0.4, numVerts=7)
#sided_point_5 = generatePolygonShapePoints(verts, 0.05)
#plt.scatter([p[0] for p in sided_point_5], [p[1] for p in sided_point_5])
#plt.scatter([p[0] for p in verts], [p[1] for p in verts], color='red')
#plt.axis([0, 1, 0, 1])
#plt.show()



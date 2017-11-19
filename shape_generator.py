# -*- coding: utf-8 -*-

import random

import matplotlib
import numpy

matplotlib.use('TkAgg')

def clip(x, amin, amax) :
     if( amin > amax ) :  return x
     elif( x < amin ) :  return amin
     elif( x > amax ) :  return amax
     else :             return x


def generatePolygon(ctrX, ctrY, aveRadius, irregularity, spikeyness, numVerts):
    irregularity = clip(irregularity, 0, 1) * 2 * numpy.math.pi / numVerts
    spikeyness = clip(spikeyness, 0, 1) * aveRadius

    # generate n angle steps
    angleSteps = []
    lower = (2 * numpy.math.pi / numVerts) - irregularity
    upper = (2 * numpy.math.pi / numVerts) + irregularity
    sum = 0
    for i in range(numVerts):
        tmp = random.uniform(lower, upper)
        angleSteps.append(tmp)
        sum = sum + tmp

    # normalize the steps so that point 0 and point n+1 are the same
    k = sum / (2 * numpy.math.pi)
    for i in range(numVerts):
        angleSteps[i] = angleSteps[i] / k

    # now generate the points
    points = []
    angle = random.uniform(0, 2 * numpy.math.pi)
    for i in range(numVerts):
        r_i = clip(random.gauss(aveRadius, spikeyness), 0, 2 * aveRadius)
        x = ctrX + r_i * numpy.math.cos(angle)
        y = ctrY + r_i * numpy.math.sin(angle)
        points.append((int(x), int(y)))

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


=======
def clip(x, min, max):
    if (min > max):
        return x
    elif (x < min):
        return min
    elif (x > max):
        return max
    else:
        return x
>>>>>>> f1b9c9133a7d35fd9e7183b5d3a0e5d984a7a26e


def generate_shape() -> [[float, float]]:
    points_number = random.randint(3, 15)
    points = generatePolygon(1500, 1500, 500, 0.35, 0.2, points_number)
    points = [[x / 2500.0, y / 2500.0] for x, y in points]
    points.append(points[0])

    xs = []
    ys = []
    for i in range(len(points) - 1):
        x_start = points[i][0]
        y_start = points[i][1]
        x_end = points[i + 1][0]
        y_end = points[i + 1][1]
        dist = numpy.math.sqrt((x_end - x_start) ** 2 + (y_end - y_start) ** 2)

        x = numpy.linspace(x_start, x_end, numpy.math.floor(dist / 0.01))
        y = numpy.linspace(y_start, y_end, numpy.math.floor(dist / 0.01))

        for x_ in x:
            xs.append(x_)

        for y_ in y:
            ys.append(y_)

    shape = []
    for x, y in zip(xs, ys):
        shape.append([x, y])

    return shape

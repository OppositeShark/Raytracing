# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 09:17:07 2022

@author: degog
"""

from PIL import Image
import random
import math
import time

randColor = lambda : (random.randint(0, 255),random.randint(0, 255),random.randint(0, 255))
multColor = lambda c, n: (c[0]*n, c[1]*n, c[2]*n)
addColor = lambda c1, c2: (c1[0]+c2[0], c1[1]+c2[1], c1[2]+c2[2])
lerpColor = lambda c1, c2, n: addColor(multColor(c1, 1-n), multColor(c2, n))
size = (1000, 1000)
centerImg = (size[0]/2, size[1]/2)
mode = "RGB"
img = Image.new(mode, size)
load = img.load()

sky = Image.open(r"C:\Users\degog\Python\RayTracing\skyImage.jpg")
skyScale = 500
skyload = sky.load()

class point():
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def add(self, p):
        return point(self.x + p.x, self.y + p.y, self.z + p.z)
    
    def __str__(self):
        return str((self.x, self.y, self.z))
    
    def __repr__(self):
        return str(self)

class vector():
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    def dot(self, v):
        return (self.x*v.x) + (self.y*v.y) + (self.z*v.z)
    
    def add(self, v):
        return vector(self.x+v.x, self.y+v.y, self.z+v.z)
    
    def sub(self, v):
        return vector(self.x-v.x, self.y-v.y, self.z-v.z)
    
    def cross(self, v):
        x = (self.y*v.z) - (self.z*v.y)
        y = (self.z*v.x) - (self.x*v.z)
        z = (self.x*v.y) - (self.y*v.x)
        return vector(x,y,z)
    
    def getVectFromPoints(p1, p2):
        x = p2.x - p1.x
        y = p2.y - p1.y
        z = p2.z - p1.z
        return vector(x,y,z)
    
    def getDist(self):
        return math.sqrt((self.x*self.x) + (self.y*self.y) + (self.z*self.z))
    
    def scale(self, s):
        return vector(self.x*s, self.y*s, self.z*s)
    
    def getVecWithDist(self, d):
        dist = self.getDist()
        x = self.x/dist*d
        y = self.y/dist*d
        z = self.z/dist*d
        return vector(x,y,z)
        
    def __str__(self):
        return str((self.x, self.y, self.z))
    
    def __repr__(self):
        return "Vector"+str(self)

class ray():
    def __init__(self, point, vector):
        self.point = point
        self.vector = vector
        
    def getDest(self):
        return self.point.add(self.vector)
    
    def __str__(self):
        return str(self.point) + "," + str(self.vector) 
  
class light():
    lights = []
    def __init__(self, point, brightness, color):
        light.lights.append(self)
        self.point = point
        self.brightness = brightness
        self.distScale = 1-(0.5/self.brightness)
        self.color = color
    
    def calcLight(self, dist, color):
        bright = math.pow(self.distScale, dist)
        color = lerpColor(color, self.color, bright)
        return multColor(color, bright)
    
class objects():
    objects = []
    def __init__(self):
        objects.objects.append(self)
        self.color = BLACK
        self.opacity = 1.0
        
    def setColor(self, color):
        self.color = color
        
    def setOpacity(self, num):
        self.opacity = num
        
    iterations = 10
    def intersect(r):
        color = (0,0,0)
        opacity = 0
        objn = None #Object that was last chosen, prevent reflect onto self
        for i in range(objects.iterations):
            #Finding the closest intersection
            obj, vec, objn = objects.calcCollision(r, objn)
            #Coloring point
            if obj == None: #Hits nothing
                v = r.vector
                if v.z != 0:
                    x = int(v.x/v.z*skyScale)%sky.size[0]
                    y = int(v.y/v.z*skyScale)%sky.size[1]
                    addedColor = skyload[x,y]
                else:
                    addedColor = (100, 100, 255)
                percentColor = (1-opacity)
                color = addColor(color, multColor(addedColor, percentColor))
                return color
            else:#If reflected
                #Color with object
                addedColor = obj.color
                percentColor = (1-opacity)*(obj.opacity)
                opacity += percentColor
                #Get correct ray/segment
                r.vector = vec
                p = r.getDest()
                #Calculate lights
                newColor = None
                for nl, lit in enumerate(light.lights):
                    rayToLight = ray(p, vector.getVectFromPoints(p, lit.point))
                    if not objects.willCollide(rayToLight, None):
                        calcColor = lit.calcLight(r.vector.getDist(), addedColor)
                        if newColor == None:
                            newColor = calcColor
                        else:
                            newColor = lerpColor(calcColor, newColor, 1/(nl+1))
                    else:
                        newColor = (0,0,0)
                if newColor != None:
                    addedColor = newColor
                color = addColor(color, multColor(addedColor, percentColor))
                r = ray(p, obj.reflection(p, r.vector))
            #Calc reflection using Vector/segment directly to object
        return color
    
    def calcCollision(r, objn):
        obj = None
        vec = None
        minDist = float("inf")
        for n, o in enumerate(objects.objects):
            if n != objn:
                ints = o.intersect(r)
                if ints != None:
                    dist = ints.getDist()
                    if dist < minDist:
                        obj = o
                        objn = n
                        vec = ints
                        minDist = dist
        return obj, vec, objn
    
    def willCollide(r, objn):
        for n, o in enumerate(objects.objects):
            if n != objn:
                ints = o.intersect(r)
                if ints != None:
                    return True
        return False

class sphere(objects):
    def __init__(self, center, radius):
        objects.__init__(self)
        self.center = center
        self.radius = radius
        
    def intersect(self, r):
        vToCenter = vector.getVectFromPoints(r.point, self.center)
        distToCenter = vToCenter.getDist()
        if distToCenter != 0: #If ray is coming from the center
            #Geometric property of circles and points
            sinVal = self.radius/distToCenter
            if sinVal < 1:
                maxAng = math.asin(sinVal)
            else:
                maxAng = math.pi/2
            dot = vToCenter.dot(r.vector)/r.vector.getDist()/distToCenter
            if dot > 1:
                ang = 0
            elif dot < -1:
                ang = math.pi
            else:
                ang = math.acos(dot) #Angle between vector to center vs vector to sphere
            if(ang > maxAng):
                return None
        else:
            ang = 0 #Looking directly ahead
        #Solving using law of cosines + quadratic formula
        #c*c = a*a + b*b - 2*a*b*cos(C)
        #a*a - 2*b*cos(C)*a + b*b-c*c = 0
        #(-b+-sqrt(b*b - 4*a*c))/(2*a)
        b = -2*math.cos(ang)*distToCenter
        c = (distToCenter*distToCenter) - (self.radius*self.radius)
        deter = (b*b) - (4*c)
        if(deter < 0):
            distToSphere = -b/2
        else:
            distToSphere = (-b-math.sqrt(deter))/2
        
        return r.vector.getVecWithDist(distToSphere)
    
    def reflection(self, p, v):
        toCenter = vector.getVectFromPoints(p, self.center)
        #assert abs(toCenter.getDist() - self.radius) < 0.0001
        oppCenter = toCenter.scale(toCenter.dot(v)/self.radius)
        parPerp = v.sub(oppCenter)
        return (oppCenter.scale(-1)).add(parPerp)
    
    def __str__(self):
        return "Sphere("+ str(self.center) + ", r:" + str(self.radius) + ")"
    
    def __repr__(self):
        return str(self)
    
class floor(objects):
    def __init__(self, height):
        objects.__init__(self)
        self.height = height
        
    def intersect(self, r):
        diff = self.height - r.point.z
        if diff == 0:
            return None
        elif diff > 0:
            if r.vector.z <= 0:
                return None
        else:
            if r.vector.z >= 0:
                return None
        return r.vector.scale(diff/r.vector.z)
    
    def reflection(self, p, v):
        #assert abs(p.z - self.height) < 0.0001
        return vector(v.x, v.y, -v.z)
    
    def __str__(self):
        return "Floor(%.2f)" %self.height
    
    def __repr__(self):
        return str(self)
        
BLACK = (0,0,0)
WHITE = (255,255,255)

center = point(-5,1,5.5)
fovX = 45/180*math.pi
fovY = 45/180*math.pi

lit = light(point(0, 10, 20), 60, (255, 255, 255))

lit = light(point(0, -10, 20), 60, (255, 0, 0))

sph = sphere(point(10, -3, 5), 4)
sph.setColor((255,0,0))
sph.setOpacity(0.1)

sph = sphere(point(12, 5, 6), 5)
sph.setColor((0, 255, 0))
sph.setOpacity(0.8)

sph = sphere(point(5, 5, 7), 2)
sph.setColor((0, 0, 255))
sph.setOpacity(0.6)

sph = sphere(point(3, 5, 0), 1)
sph.setColor((255, 255, 255))
sph.setOpacity(0.9)

flr = floor(0)
flr.setColor((0,0,0))
flr.setOpacity(0.5)

startTime = time.time()
xScl = math.tan(fovX)
yScl = -math.tan(fovY)
for x in range(size[0]):
    print(x/size[0]*100, "%")
    xnorm = 2*(x-centerImg[0])/size[0] #[-1,1]
    nx = xnorm*xScl
    for y in range(size[1]):
        ynorm = 2*(y-centerImg[0])/size[1] #[-1,1]
        ny = ynorm*yScl
        r = ray(center, vector(1, nx, ny))
        #print("-----")
        #print(x,y)
        load[x,y] = tuple([int(i) for i in objects.intersect(r)])

print("Time Taken: %.2f" %(time.time()-startTime))
img.show()
img.save("rayTrace.png")
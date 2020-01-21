import pygame
import time
import random
import math
import matplotlib
from pygame.locals import *
import matplotlib.backends.backend_agg as agg
import pylab

pygame.init()
screen = pygame.display.set_mode((1600, 800), DOUBLEBUF)
clock = pygame.time.Clock()
blobs = []
foods = []
sameBool = False
time = 0
blobPop = [80]
blobAvgSpeed = []
blobAvgSpeedVar = 0
blobAvgDetect = []
blobAvgDetectVar = 0

def graph(graphList):
    matplotlib.use("Agg")
    
    fig = pylab.figure(figsize=[4, 4], dpi=100)
    ax = fig.gca()
    ax.plot(graphList)
    
    canvas = agg.FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = renderer.tostring_rgb()
    
    size = canvas.get_width_height()
    return pygame.image.fromstring(raw_data, size, "RGB")

surf = graph(blobAvgSpeed)
turf = graph(blobPop)
murf = graph(blobAvgDetect)

def collision(rleft, rtop, width, height,   # rectangle definition
              center_x, center_y, radius):  # circle definition
    """ Detect collision between a rectangle and circle. """

    # complete boundbox of the rectangle
    rright, rbottom = rleft + width/2, rtop + height/2

    # bounding box of the circle
    cleft, ctop     = center_x-radius, center_y-radius
    cright, cbottom = center_x+radius, center_y+radius

    # trivial reject if bounding boxes do not intersect
    if rright < cleft or rleft > cright or rbottom < ctop or rtop > cbottom:
        return False  # no collision possible

    # check whether any point of rectangle is inside circle's radius
    for x in (rleft, rleft+width):
        for y in (rtop, rtop+height):
            # compare distance between circle's center point and each point of
            # the rectangle with the circle's radius
            if math.hypot(x-center_x, y-center_y) <= radius:
                return True  # collision detected

    # check if center of circle is inside rectangle
    if rleft <= center_x <= rright and rtop <= center_y <= rbottom:
        return True  # overlaid

    return False  # no collision detected

def spawnFood():
    foodNumber = 200
    while len(foods) < foodNumber:
        sameBool = False
        food_thing = foodClass(random.randint(20, 760), random.randint(20, 760))
        for food in foods:
            if food.location == food_thing.location:
                sameBool = True
        if not sameBool:
            foods.append(food_thing)

def isOccupied(coord, blobMove):
    for blob in blobs:
        if blobMove != blob and blob.rect.colliderect(pygame.Rect(coord[0], coord[1], 20, 20)):
            return True
    return False

def blobCount(moveRect):
    count = 0
    for blob in blobs:
        if blob.rect.colliderect(moveRect):
            count += 1
    return count

def getFoodNeeded(blob):
    foodNeeded = int(blob.speed/2)**3
    if foodNeeded < 1:
        foodNeeded = 1
    return foodNeeded + int(blob.detectParams[1]/100)

def getPriority(canGo, blob):
    options = [blob.y, 780-blob.y, blob.x, 780-blob.x]
    priorityDict = {}
    detectParams = blob.detectParams
    choices = ["up", "left", "right", "down"]
    if blob.food < getFoodNeeded(blob) + 2:
        if options.index(min(options)) == 0: priority = "down"
        elif options.index(min(options)) == 1: priority = "up"
        elif options.index(min(options)) == 2: priority = "right"
        elif options.index(min(options)) == 3: priority = "left"
    else:
        if options.index(max(options)) == 0: priority = "up"
        elif options.index(max(options)) == 1: priority = "down"
        elif options.index(max(options)) == 2: priority = "left"
        elif options.index(max(options)) == 3: priority = "right"
    if priority in canGo:
        return priority
    for option in canGo:
        if option == "up": priorityDict["up"] = blobCount(pygame.Rect(blob.x-blob.detectParams[0], blob.y-blob.detectParams[0], blob.detectParams[1], blob.detectParams[1]/2))
        if option == "down": priorityDict["down"] = blobCount(pygame.Rect(blob.x-blob.detectParams[0], blob.y-blob.detectParams[0]+(detectParams[1]/2), blob.detectParams[1], blob.detectParams[1]/2))
        if option == "left": priorityDict["left"] = blobCount(pygame.Rect(blob.x-blob.detectParams[0], blob.y-blob.detectParams[0], blob.detectParams[1]/2, blob.detectParams[1]))
        if option == "right": priorityDict["right"] = blobCount(pygame.Rect(blob.x-blob.detectParams[0]+(detectParams[1]/2), blob.y-blob.detectParams[0], blob.detectParams[1]/2, blob.detectParams[1]))
    return min(priorityDict, key=priorityDict.get)

def moveAI(canGo, priority, blob):
    coords = blob.location
    if len(canGo) == 1:
        return False
    else:
        if priority == "up": moveInfo=[coords[1] > 5, not isOccupied([coords[0], coords[1]-5], blob), 1]
        elif priority == "down": moveInfo=[coords[1] < 775, not isOccupied([coords[0], coords[1]+5], blob), 2]
        elif priority == "left": moveInfo=[coords[0] > 5, not isOccupied([coords[0]-5, coords[1]], blob), 3]
        elif priority == "right": moveInfo=[coords[0] < 775, not isOccupied([coords[0]+5, coords[1]], blob), 4]
        if moveInfo[0] and moveInfo[1]:
            return moveInfo[2]
        else:
            canGo.remove(priority)
            return moveAI(canGo, getPriority(canGo, blob), blob)

def eatFood(blob):
    for food in foods:
        if collision(blob.x, blob.y, 20, 20, food.x, food.y, 10):
            #if not blob.food >= getFoodNeeded(blob) + 2:
            foods.remove(food)
            blob.food += 1
            blob.energy += 100

class blobClass(object):
    blobTag = 1
    def __init__(self, x, y, speed, detectGene, reproduced = False):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(self.x, self.y, 20, 20)
        self.location = [self.x, self.y]
        self.tracked = False
        self.moving = False
        self.target = []
        self.food = 0
        self.speed = speed
        self.number = blobClass.blobTag
        self.reproduced = reproduced
        self.detectGene = detectGene
        self.detectParams = [(detectGene-3*30-20)/2, detectGene-3*30]
        self.energy = 200
        self.moves = []
        blobClass.blobTag += 1

    def move(self, move, moving=False, goHomeVar=False):
        if not moving and not goHomeVar:
            self.location = [self.x, self.y]
            if move == None: go = moveAI(["up", "left", "right", "down"], getPriority(["up", "left", "right", "down"], self), self)
            elif move == 1: go = moveAI(["up", "left", "right", "down"], "up", self)
            elif move == 2: go = moveAI(["down", "right", "left", "up"], "down", self)
            elif move == 3: go = moveAI(["right", "up", "down", "left"], "left", self)
            elif move == 4: go = moveAI(["left", "up", "down", "right"], "right", self)
            if go == 1: 
                self.y -= 5
                eatFood(self)
                #if self.tracked: print("Blob " + str(self.number) + " moved up")
            elif go == 2: 
                self.y += 5
                eatFood(self)
                #if self.tracked: print("Blob " + str(self.number) + " moved down")
            elif go == 3: 
                self.x -= 5
                eatFood(self)
                #if self.tracked: print("Blob " + str(self.number) + " moved left")
            elif go == 4: 
                self.x += 5
                eatFood(self)
                #if self.tracked: print("Blob " + str(self.number) + " moved right")
            self.location = [self.x, self.y]

        elif not goHomeVar and moving:
            target = self.target
            self.location = [self.x, self.y]
            for food in foods:
                if food.location == target:
                    if not collision(self.x, self.y, 20, 20, food.x, food.y, 10):
                        if not abs(self.location[0]-target[0]) < 5:
                            if target[0] > self.location[0]: self.move(4)
                            if target[0] < self.location[0]: self.move(3)
                        elif not abs(self.location[1]-target[1]) < 5:
                            if target[1] > self.location[1]: self.move(2)
                            if target[1] < self.location[1]: self.move(1)
                    else:
                        self.moving = False
                        eatFood(self)
                        if self.tracked: print("Blob " + str(self.number) + " got to food")
                        self.move(random.randint(1, 4))
                    break
                elif food.location != target and foods.index(food) == len(foods) - 1:
                    self.moving = False
                    self.move(random.randint(1, 4))
        else:
            options = [self.y, 780-self.y, self.x, 780-self.x]
            if min(options) > 4:
                self.move(options.index(min(options))+1, False, False)

    def detect(self):
        if not self.moving:
            self.target = []
            for food in foods:
                if collision(self.x-self.detectParams[0], self.y-self.detectParams[0], self.detectParams[1], self.detectParams[1], food.x, food.y, 10):
                    self.moving = True
                    if len(self.target) < 1 or abs(food.y-self.y) + abs(food.x-self.x) < abs(self.target[0]-self.x) + abs(self.target[1]-self.y):
                        self.target = food.location
                    #if self.tracked: print("Blob " + str(self.number) + " detected food nearby")

    def reproduce(self):
        self.food -= 2
        minimumSpeed = self.speed/1.25
        if minimumSpeed < 1:
            minimumSpeed = 1
        maximumSpeed = self.speed*1.25
        location = [random.randint(20, 760), random.randint(20, 760)]
        if self.x + 30 <= 770 and not isOccupied([self.x+30, self.y], None):
            location = [self.x+30, self.y]
        elif self.y + 30 <= 770 and not isOccupied([self.x, self.y+30], None):
            location = [self.x, self.y+30]
        elif self.y - 30 >= 30 and not isOccupied([self.x, self.y-30], None):
            location = [self.x, self.y-30]
        elif self.x - 30 >= 30 and not isOccupied([self.x-30, self.y], None):
            location = [self.x-30, self.y]
        else:
            location = None    
        
        if location != None:
            blobs.append(blobClass(location[0], location[1], random.randint(int(minimumSpeed*100), int(maximumSpeed*100))/100, random.randint(self.detectGene-40, self.detectGene+40)))
            print("Blob " + str(self.number) + " reproduced")

    def update(self):
        self.rect = pygame.Rect(self.x, self.y, 20, 20)
        self.rect.clamp_ip(screen.get_rect())
        color = 30 * self.speed
        if color > 255:
            color = 255
        color = (0, color, 0)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, color, pygame.Rect(self.x-self.detectParams[0], self.y-self.detectParams[0], self.detectParams[1], self.detectParams[1]), 1)

class foodClass(object):
    def __init__(self, x, y):
        self.x = x 
        self.y = y
        self.location = [self.x, self.y]

    def update(self):
        pygame.draw.circle(screen, (255, 0, 0), (self.x, self.y), 10)

while len(blobs) < 80:
    sameBool = False
    ting = random.randint(1, 4)
    if ting == 1: player = blobClass(0, random.randint(0, 780), 3.5, 160)
    if ting == 2: player = blobClass(780, random.randint(0, 780), 3.5, 160)
    if ting == 3: player = blobClass(random.randint(0, 780), 0, 3.5, 160)
    if ting == 4: player = blobClass(random.randint(0, 780), 780, 3.5, 160)
    for blob in blobs:
        if blob.rect.colliderect(player.rect): 
            sameBool = True
    if not sameBool:
        blobs.append(player)

for blob in blobs:
    blobAvgSpeedVar += blob.speed
    blobAvgDetectVar += blob.detectParams[1]

blobAvgSpeed.append(blobAvgSpeedVar/len(blobs))
blobAvgDetect.append(blobAvgDetectVar/len(blobs))

spawnFood()

'''
for thing in blobs:
    thing.tracked = True
while True:
    pygame.display.flip()
    screen.fill((0, 0, 0))
    #pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(200, 200, 20, 20))
    #pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(200, 200, 20, 10))
    #pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(200, 200, 10, 20))
    pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(200+20, 200, 20, 40))
    #pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(200, 200, 20, 20))

'''
while True:
    pygame.display.flip()
    screen.fill((0, 0, 0))

    if time == 275:
        time = 0
        blobPop.append(len(blobs))
        blobAvgSpeedVar = 0
        blobAvgDetectVar = 0
        for blob in blobs:
            blobAvgSpeedVar += blob.speed
            blobAvgDetectVar += blob.detectParams[1]

        blobAvgSpeed.append(blobAvgSpeedVar/len(blobs))
        blobAvgDetect.append(blobAvgDetectVar/len(blobs))

        surf = graph(blobAvgSpeed)
        turf = graph(blobPop)
        murf = graph(blobAvgDetect)
        spawnFood()

    elif time == 225:
        for blob in blobs:
            foodNeeded = getFoodNeeded(blob)
            if blob.food >= foodNeeded:
                blob.food -= foodNeeded
            #else:
                #print("Blob " + str(blob.number) + " died from hunger")
                #blobs.remove(blob)
        
        foods = []
        for blob in blobs:
            blob.detect()
            blob.update()
        time += 1

    elif time == 245:
        for food in foods:
            food.update()
        for blob in blobs:
            if blob.food > 1:
                blob.reproduce()
        for blob in blobs:
            blob.food = 0
            blob.energy = 100
            blob.detect()
            blob.update()
        time +=1

    #Reset phase 225-275
    elif 275 > time > 245 or 245 > time > 225:
        for food in foods:
            food.update()
        for blob in blobs:
            blob.update()
        time += 1
    #Go home phase 150-225
    elif 225 > time > 150:
        for food in foods:
            food.update()
        for blob in blobs:
            for x in range(int(blob.speed)):
                blob.move(1, False, True)
                blob.update()
        time += 1
    #Normal moving phase 0-150
    else:
        for food in foods:
            food.update()
        for blob in blobs:
            direction = random.randint(1, 4)
            for x in range(int(blob.speed)):
                blob.detect()
                blob.move(direction, blob.moving)
                blob.update()
            blob.energy -= blob.speed+int(blob.detectParams[1]/100)
            if blob.energy < 1:
                blobs.remove(blob)
        time += 1

    
    screen.blit(surf, (800, 0))
    screen.blit(turf, (800, 400))
    screen.blit(murf, (1200, 0))

    clock.tick(60)
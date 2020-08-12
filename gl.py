import struct
import random
from obj import Obj
from collections import namedtuple


V2 = namedtuple('Point2', ['x', 'y'])
V3 = namedtuple('Point3', ['x', 'y', 'z'])

def sum(v0, v1):
  #suma de V3
  return V3(v0.x + v1.x, v0.y + v1.y, v0.z + v1.z)

def sub(v0, v1):
  #resta de V3
  return V3(v0.x - v1.x, v0.y - v1.y, v0.z - v1.z)

def mul(v0, k):
  #multiplicacion de V3 con constante
  return V3(v0.x * k, v0.y * k, v0.z *k)

def dot(v0, v1):
  #producto punto de dos V3
  return v0.x * v1.x + v0.y * v1.y + v0.z * v1.z

def cross(v0, v1):
  #producto cruz de dos V3
  return V3(
    v0.y * v1.z - v0.z * v1.y,
    v0.z * v1.x - v0.x * v1.z,
    v0.x * v1.y - v0.y * v1.x,
  )

def length(v0):
  #Largo del V3
  return (v0.x**2 + v0.y**2 + v0.z**2)**0.5

def norm(v0):
  #vector normal de una V3
  v0length = length(v0)

  if not v0length:
    return V3(0, 0, 0)

  return V3(v0.x/v0length, v0.y/v0length, v0.z/v0length)

def bbox(*vertices):
  # devuelve el bounding box de dos V2
  xs = [ vertex.x for vertex in vertices ]
  ys = [ vertex.y for vertex in vertices ]
  xs.sort()
  ys.sort()

  return V2(xs[0], ys[0]), V2(xs[-1], ys[-1])

def barycentric(A, B, C, P):
  #Coordenadas baricentricas de 3 V2
  bary = cross(
    V3(C.x - A.x, B.x - A.x, A.x - P.x), 
    V3(C.y - A.y, B.y - A.y, A.y - P.y)
  )

  if abs(bary[2]) < 1:
    return -1, -1, -1 

  return (
    1 - (bary[0] + bary[1]) / bary[2], 
    bary[1] / bary[2], 
    bary[0] / bary[2]
  )

def char(c):
  return struct.pack('=c', c.encode('ascii'))

def word(w):
  return struct.pack('=h', w)

def dword(d):
  return struct.pack('=l', d)

def color(r, g, b):
  return bytes([b, g, r])


BLACK = color(0, 0, 0)
WHITE = color(255, 255, 255)

class Render(object):
  def __init__(self, width, height):
    self.width = width
    self.height = height
    self.current_color = WHITE
    self.glClear()

  def glClear(self):
    self.framebuffer = [
      [BLACK for x in range(self.width)] 
      for y in range(self.height)
    ]
    self.zbuffer = [
      [-float('inf') for x in range(self.width)]
      for y in range(self.height)
    ]

  def finish(self, filename):
    f = open(filename, 'bw')

    #14 bytes
    f.write(char('B'))
    f.write(char('M'))
    f.write(dword(14 + 40 + self.width * self.height * 3))
    f.write(dword(0))
    f.write(dword(14 + 40))

    #40 bytes
    f.write(dword(40))
    f.write(dword(self.width))
    f.write(dword(self.height))
    f.write(word(1))
    f.write(word(24))
    f.write(dword(0))
    f.write(dword(self.width * self.height * 3))
    f.write(dword(0))
    f.write(dword(0))
    f.write(dword(0))
    f.write(dword(0))

    for x in range(self.height):
      for y in range(self.width):
        f.write(self.framebuffer[x][y])

    f.close()

  def set_color(self, color):
    self.current_color = color

  def point(self, x, y, color):
    try:
      self.framebuffer[y][x] = color or self.current_color
    except:
      pass
    
  def line(self, start, end, color):
    x1, y1 = start.x, start.y
    x2, y2 = end.x, end.y

    dy = abs(y2 - y1)
    dx = abs(x2 - x1)
    steep = dy > dx

    if steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1

    dy = abs(y2 - y1)
    dx = abs(x2 - x1)

    offset = 0
    threshold = dx

    y = y1
    for x in range(x1, x2 + 1):
        if steep:
            self.point(y, x, color)
        else:
            self.point(x, y, color)
        
        offset += dy * 2
        if offset >= threshold:
            y += 1 if y1 < y2 else -1
            threshold += dx * 2

  def triangle(self, A, B, C, color):
    bbox_min, bbox_max = bbox(A, B, C)

    for x in range(bbox_min.x, bbox_max.x + 1):
      for y in range(bbox_min.y, bbox_max.y + 1):
        w, v, u = barycentric(A, B, C, V2(x, y))
        if w < 0 or v < 0 or u < 0:  #0 es valido
          continue
        
        z = A.z * w + B.z * v + C.z * u

        if z > self.zbuffer[x][y]:
          self.point(x, y, color)
          self.zbuffer[x][y] = z

  def transform(self, vertex, translate=(0, 0, 0), scale=(1, 1, 1)):
    #devuelve el vector escalado y traladado
    return V3(
      round((vertex[0] + translate[0]) * scale[0]),
      round((vertex[1] + translate[1]) * scale[1]),
      round((vertex[2] + translate[2]) * scale[2])
    )
  def shader(self, x, y):
    
    if(y>=0 and y<=25  and x%2==1):
      return color(187, 122, 104)
    elif(y>=26 and y<=100 and x%2==0):
      return color(205, 138, 116)
    #Mancha
    elif(y>=101 and y<=200 and x<=260 and x>=190 and x%3==1 ):
      return color(233, 201, 173)
    elif(y>=101 and y<=200 and x<=260 and x>=190 and (x%3==0 or x%3==2)):
      return color(214, 180, 163)
    elif(y>=101 and y<=200 and x<=280 and x>=260 and x%2==0):
      return color(130, 87, 79)
    elif(y>=101 and y<=200 and x>=170 and x<=189 and x%2==0):
      return color(233, 201, 173)
    elif(y>=101 and y<=200 and x>=170 and x<=189 and x%2==1):
      return color(130, 87, 79)
    elif(y>=201 and y<=220 and x>=170 and x<=260 and x%2==0):
      return color(130, 87, 79)
    elif(y>=201 and y<=220 and x>=170 and x<=260 and x%2==1):
      return color(233, 201, 173)
    elif(y>=75 and y<=100 and x>=170 and x<=260 ):
      return color(130, 87, 79)
    #fin Mancha
    elif(y>=220 and x%2==1):
      return color(187, 122, 104)
    elif(y>=75 and y<=220 and x>=191 and x%2==0):
      return color(216, 140, 114)
    elif(y>=400 and y<=320 and x>=200):
      return color(255,0,0)
    else:
      return color(226, 147, 118)
    
  def load(self, filename, translate=(0, 0, 0), scale=(1, 1, 1)):
    model = Obj(filename)

    light = V3(0,0,1)

    for face in model.faces:
        vcount = len(face)

        if vcount == 3:
          f1 = face[0][0] - 1
          f2 = face[1][0] - 1
          f3 = face[2][0] - 1

          a = self.transform(model.vertices[f1], translate, scale)
          b = self.transform(model.vertices[f2], translate, scale)
          c = self.transform(model.vertices[f3], translate, scale)

          x = min([a.x, b.x, c.x])
          y = min([a.y, b.y, c.y])
          shader = self.shader(x, y)

          normal = norm(cross(sub(b, a), sub(c, a)))
          intensity = dot(normal, norm(light))
          colorList = []
          for i in shader:
            if i * intensity > 0:
              colorList.append(round(i*intensity))
            else:
              colorList.append(10)
          colorList.reverse()

          self.triangle(a, b, c,color(colorList[0], colorList[1], colorList[2]))
        else:
          f1 = face[0][0] - 1
          f2 = face[1][0] - 1
          f3 = face[2][0] - 1
          f4 = face[3][0] - 1   

          vertices = [
            self.transform(model.vertices[f1], translate, scale),
            self.transform(model.vertices[f2], translate, scale),
            self.transform(model.vertices[f3], translate, scale),
            self.transform(model.vertices[f4], translate, scale)
          ]

          A, B, C, D = vertices

          x = min([A.x, B.x, C.x, D.x])
          y = min([A.y, B.y, C.y, D.y])
          shader = self.shader(x, y)

          normal = norm(cross(sub(B, A), sub(C, A)))
          intensity = dot(normal, norm(light))
          colorList = []
          for i in shader:
            if i * intensity > 0:
              colorList.append(round(i*intensity))
            else:
              colorList.append(10)
          colorList.reverse()

          self.triangle(A, B, C,color(colorList[0], colorList[1], colorList[2]))
          self.triangle(A, C, D,color(colorList[0], colorList[1], colorList[2]))

r = Render(800, 800)
r.load('./sphere.obj', (1, 0.5, 0.5), (300, 300, 300))
r.finish('out.bmp')
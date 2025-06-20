# zSlicer implementation

from compas.geometry import Frame, Line, Polyline
from numpy import array
from zspace.slicer import *
from z3DPSlicer.zUtil import tMatrixToFrame


class Slicer:
    def __init__(self):
        self.mesh = None
        self.startPlane = None
        self.endPlane = None

    def set_mesh(self, mesh):
        self.mesh = mesh

    def slice(self, startPlane, endPlane, step):
        
        # interpolate planes between startPlane and endPlane using c++ bind method
        # create a list of planes
        planes = []
        for i in range(step):
            tMatrix = self.interpolatePlanes(startPlane, endPlane, i/step)
            planes.append(tMatrixToFrame(tMatrix))
        
        # for each plane, slice the mesh
        contours = self.sliceMesh(planes)


        # return a list of contours
        pass

    def interpolatePlanes(self, startPlane, endPlane, t):

        # create a transformation matrix from startPlane to endPlane
        tMatrix = ......
        return interpolatePlanes(tMatrix, t)
    
    def sliceMesh(self, planes):
        # for each plane, slice the mesh
        contours = []
        for plane in planes:
            contours.append(self.sliceMesh(plane))
        return contours




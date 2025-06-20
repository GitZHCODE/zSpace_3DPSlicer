# zSlicer implementation

from compas.geometry import Frame, Line, Polyline
from numpy import array
from z3DPSlicer import zSlicer as zSlicerCpp, zMesh, zPlane
import z3DPSlicer
from z3DPSlicer.zUtil import tMatrixToFrame

class Slicer:
    def __init__(self):
        self.mesh = None
        self.startPlane = None
        self.endPlane = None
        self.cpp_slicer = zSlicerCpp()

    def set_mesh(self, mesh):
        self.mesh = mesh
        zmesh = zMesh()
        vertices = array(mesh.vertices_attributes('xyz'))
        faces = array(mesh.faces())
        zmesh.setVertices(vertices)
        zmesh.setFaces(faces)
        self.cpp_slicer.setMesh(zmesh)

    def slice(self, startPlane, endPlane, step):
        # interpolate planes between startPlane and endPlane using c++ bind method
        # create a list of planes
        planes = []
        for i in range(step):
            tMatrix = self.interpolatePlanes(startPlane, endPlane, i/step)
            planes.append(tMatrixToFrame(tMatrix))
        
        # for each plane, slice the mesh
        contours = self.sliceMesh(planes)
        return contours

    def interpolatePlanes(self, startPlane, endPlane, t):
        # create a transformation matrix from startPlane to endPlane
        # TODO: implement plane interpolation
        return startPlane
    
    def sliceMesh(self, planes):
        # for each plane, slice the mesh
        contours = []
        for plane in planes:
            zplane = zPlane()
            origin = array(plane.point)
            normal = array(plane.zaxis)
            zplane.setOrigin(origin)
            zplane.setNormal(normal)
            contour = self.cpp_slicer.slice(zplane)
            contours.append(contour)
        return contours




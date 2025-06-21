import compas
from compas.geometry import Point, Frame, Plane , Vector
from compas.datastructures import Mesh, Network

import numpy as np
from z3DPSlicer import zMesh, zGraph, zField
from compas.colors import Color

class zSlicer:
    def __init__(self):
        self.blockMesh = zMesh()
        self.sliceMesh = zMesh()
        self.startPlane = None
        self.endPlane = None
        self.planes = []
        self.contours = []
        self.fields = []

    def set_mesh(self, mesh):
        self.mesh = mesh
        self.blockMesh.from_compas_mesh(mesh)
        mesh.quads_to_triangles()
        self.sliceMesh.from_compas_mesh(mesh)

    def slice(self, start, end, steps):
        self.startPlane = Plane(start, end)
        self.endPlane = Plane(end, start)
        planes = []
        
        for t in range(steps):
            planes.append(Plane(start + (end - start) * t / steps, end))
        self.planes = planes

        for plane in planes:
            zgraph = self.sliceMesh.intersect_plane(plane.point, plane.normal)
            if zgraph is not None and zgraph.get_vertex_count() > 0:
                self.contours.append(zGraph(zgraph).to_compas_network())

    def get_planes(self):
        return self.planes

    def get_contours(self):
        return self.contours

    def get_fields(self):
        return self.fields
from z3DPSlicer._zspace import Mesh as ZSpaceMesh, get_last_error
import numpy as np
from .zGraph import zGraph

class zMesh:
    def __init__(self, compas_mesh=None):
        self.zmesh = None
        if compas_mesh is not None:
            self.from_compas_mesh(compas_mesh)

    def from_compas_mesh(self, compas_mesh):
        vertices, faces = compas_mesh.to_vertices_and_faces()
        vertices = np.array(vertices, dtype=np.float64)
        poly_counts = np.array([len(face) for face in faces], dtype=np.int32)
        poly_connections = np.array([vertex for face in faces for vertex in face], dtype=np.int32)
        self.zmesh = ZSpaceMesh()
        success = self.zmesh.create_mesh(vertices, poly_counts, poly_connections)
        if not success:
            raise Exception(f"Failed to create zSpace mesh: {get_last_error()}")
        return self

    def get_vertex_count(self):
        return self.zmesh.get_vertex_count()

    def get_face_count(self):
        return self.zmesh.get_face_count()

    def compute_geodesic_heat(self, source_vertex_id):
        source_vertices = np.array([source_vertex_id], dtype=np.int32)
        distances = np.zeros(self.zmesh.get_vertex_count(), dtype=np.float32)
        success = self.zmesh.compute_geodesic_heat(source_vertices, True, distances)
        if not success:
            raise Exception(f"Failed to compute geodesic distances: {get_last_error()}")
        return distances

    def compute_geodesic_contours(self, source_vertex_id, steps=10, dist=0.0):
        """Compute geodesic contours and return zGraph objects."""
        source_vertices = np.array([source_vertex_id], dtype=np.int32)
        try:
            contours, count = self.zmesh.compute_geodesic_contours(source_vertices, steps, dist)
            if count == 0:
                return []
            contour_graphs = []
            batch_size = 5
            for batch_start in range(0, count, batch_size):
                batch_end = min(batch_start + batch_size, count)
                for i in range(batch_start, batch_end):
                    try:
                        graph = zGraph(contours[i])
                        contour_graphs.append(graph)
                    except Exception:
                        continue
                import gc
                gc.collect()
            return contour_graphs
        except Exception:
            return [] 
from z3DPSlicer._zspace import Mesh as ZSpaceMesh, get_last_error
import numpy as np
from .zGraph import zGraph
from compas.geometry import Point, Polygon
from compas.datastructures import Mesh as CompasMesh

class zMesh:
    def __init__(self, zmesh_handle=None):
        if zmesh_handle is None:
            self.zmesh = ZSpaceMesh()
        elif isinstance(zmesh_handle, ZSpaceMesh):
            self.zmesh = zmesh_handle
        else:
            raise ValueError("zmesh_handle must be a ZSpaceMesh instance")

    def is_valid(self):
        """Check if the mesh is valid."""
        return self.zmesh.is_valid()

    def get_vertex_count(self):
        """Get the number of vertices in the mesh."""
        return self.zmesh.get_vertex_count()

    def get_face_count(self):
        """Get the number of faces in the mesh."""
        return self.zmesh.get_face_count()

    def create_mesh(self, vertex_positions, poly_counts, poly_connections):
        """Create a mesh from vertex positions, polygon counts, and connections."""
        return self.zmesh.create_mesh(vertex_positions, poly_counts, poly_connections)

    def get_mesh_data(self):
        """Get the mesh data as (vertices, poly_counts, poly_connections) tuple."""
        return self.zmesh.get_mesh_data()

    def compute_geodesic_heat(self, source_vertex_ids, normalised=True):
        """Compute geodesic heat from source vertices."""
        distances = np.zeros(self.get_vertex_count(), dtype=np.float32)
        success = self.zmesh.compute_geodesic_heat(source_vertex_ids, normalised, distances)
        if not success:
            raise Exception(f"Failed to compute geodesic heat: {get_last_error()}")
        return distances

    def compute_geodesic_heat_interpolated(self, start_vertex_ids, end_vertex_ids, weight):
        """Compute interpolated geodesic heat between start and end vertices."""
        distances = np.zeros(self.get_vertex_count(), dtype=np.float32)
        success = self.zmesh.compute_geodesic_heat_interpolated(start_vertex_ids, end_vertex_ids, weight, distances)
        if not success:
            raise Exception(f"Failed to compute interpolated geodesic heat: {get_last_error()}")
        return distances

    def compute_geodesic_contours(self, source_vertex_ids, steps, dist):
        """Compute geodesic contours from source vertices."""
        return self.zmesh.compute_geodesic_contours(source_vertex_ids, steps, dist)

    def compute_geodesic_contours_interpolated(self, start_vertex_ids, end_vertex_ids, steps, dist):
        """Compute geodesic contours between start and end vertices with interpolation."""
        start_array = np.array(start_vertex_ids, dtype=np.int32)
        end_array = np.array(end_vertex_ids, dtype=np.int32)
        contours, count = self.zmesh.compute_geodesic_contours_interpolated(start_array, end_array, steps, dist)
        return [zGraph(zgraph) for zgraph in contours], count

    def set_handle(self, handle):
        """Set the internal handle."""
        return self.zmesh.set_handle(handle)

    def get_handle(self):
        """Get the internal handle."""
        return self.zmesh.get_handle()

    def to_compas_polygons(self):
        """Convert zSpace mesh to COMPAS Polygon objects."""
        vertices_array, poly_counts_array, poly_connections_array = self.zmesh.get_mesh_data()
        vertices = vertices_array.tolist()
        poly_counts = poly_counts_array.tolist()
        poly_connections = poly_connections_array.tolist()
        
        if len(vertices) == 0 or len(poly_counts) == 0:
            return []
        
        points = [Point(*vertex) for vertex in vertices]
        polygons = []
        
        connection_index = 0
        for poly_count in poly_counts:
            if poly_count >= 3:  # Need at least 3 vertices for a polygon
                polygon_vertices = []
                for i in range(poly_count):
                    if connection_index < len(poly_connections):
                        vertex_idx = poly_connections[connection_index]
                        if 0 <= vertex_idx < len(points):
                            polygon_vertices.append(points[vertex_idx])
                        connection_index += 1
                
                if len(polygon_vertices) >= 3:
                    polygons.append(Polygon(polygon_vertices))
        
        return polygons

    def to_compas_mesh(self):
        """Convert zSpace mesh to COMPAS Mesh datastructure."""
        try:
            vertices_array, poly_counts_array, poly_connections_array = self.zmesh.get_mesh_data()
            vertices = vertices_array.tolist()
            poly_counts = poly_counts_array.tolist()
            poly_connections = poly_connections_array.tolist()
            
            if len(vertices) == 0:
                return CompasMesh()
            
            # Create COMPAS Mesh
            mesh = CompasMesh()
            
            # Add vertices
            for i, vertex_coords in enumerate(vertices):
                try:
                    point = Point(*vertex_coords)
                    mesh.add_vertex(i, x=point.x, y=point.y, z=point.z)
                except Exception as e:
                    continue
            
            # Add faces
            connection_index = 0
            face_count = 0
            for face_idx, poly_count in enumerate(poly_counts):
                try:
                    if poly_count >= 3:  # Need at least 3 vertices for a face
                        face_vertices = []
                        for i in range(poly_count):
                            if connection_index < len(poly_connections):
                                vertex_idx = poly_connections[connection_index]
                                if 0 <= vertex_idx < len(vertices):
                                    face_vertices.append(vertex_idx)
                                connection_index += 1
                            else:
                                break
                        
                        if len(face_vertices) >= 3:
                            # Check if all vertices exist in the mesh
                            valid_vertices = [v for v in face_vertices if v in mesh.vertices()]
                            if len(valid_vertices) >= 3:
                                mesh.add_face(valid_vertices)
                                face_count += 1
                    else:
                        # Skip this face and advance connection_index
                        connection_index += poly_count
                except Exception as e:
                    # Skip this face and advance connection_index
                    connection_index += poly_count
                    continue
            
            return mesh
            
        except Exception as e:
            # Return empty mesh as fallback
            return CompasMesh()

    def from_compas_mesh(self, compas_mesh):
        """Create zSpace mesh from COMPAS mesh."""
        vertices, faces = compas_mesh.to_vertices_and_faces()
        vertices = np.ascontiguousarray(np.array(vertices, dtype=np.float32))
        poly_counts = np.ascontiguousarray(np.array([len(face) for face in faces], dtype=np.int32))
        poly_connections = np.ascontiguousarray(np.array([vertex for face in faces for vertex in face], dtype=np.int32))
        
        # Debug: Print mesh data
        print(f"Converting COMPAS mesh to zSpace mesh:")
        print(f"  Vertices: {len(vertices)} points, dtype={vertices.dtype}, shape={vertices.shape}, contiguous={vertices.flags['C_CONTIGUOUS']}")
        print(f"  Faces: {len(faces)} faces")
        print(f"  Poly counts: {poly_counts}, dtype={poly_counts.dtype}, shape={poly_counts.shape}, contiguous={poly_counts.flags['C_CONTIGUOUS']}")
        print(f"  Poly connections: {len(poly_connections)} indices, dtype={poly_connections.dtype}, shape={poly_connections.shape}, contiguous={poly_connections.flags['C_CONTIGUOUS']}")
        
        # Check if vertices are within reasonable bounds
        if len(vertices) > 0:
            min_coords = np.min(vertices, axis=0)
            max_coords = np.max(vertices, axis=0)
            print(f"  Vertex bounds: X[{min_coords[0]:.3f}, {max_coords[0]:.3f}], Y[{min_coords[1]:.3f}, {max_coords[1]:.3f}], Z[{min_coords[2]:.3f}, {max_coords[2]:.3f}]")
        
        self.zmesh = ZSpaceMesh()
        success = self.zmesh.create_mesh(vertices, poly_counts, poly_connections)
        if not success:
            raise Exception(f"Failed to create zSpace mesh: {get_last_error()}")
        
        # Debug: Check if zSpace mesh was created correctly
        print(f"  zSpace mesh created: {self.zmesh.is_valid()}")
        print(f"  zSpace vertex count: {self.zmesh.get_vertex_count()}")
        print(f"  zSpace face count: {self.zmesh.get_face_count()}")
        
        return self

    def intersect_plane(self, origin, normal):
        """Intersect mesh with a plane and return a zGraph if successful, else None."""
        origin_array = np.array(origin, dtype=np.float32)
        normal_array = np.array(normal, dtype=np.float32)
        graph = self.zmesh.intersect_plane(origin_array, normal_array)
        return graph
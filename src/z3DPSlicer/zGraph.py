from z3DPSlicer._zspace import Graph as ZSpaceGraph
from compas.geometry import Point
from compas.datastructures import Network
import numpy as np

class zGraph:
    def __init__(self, zgraph_handle=None):
        if zgraph_handle is None:
            self.zgraph = ZSpaceGraph()
        elif isinstance(zgraph_handle, ZSpaceGraph):
            self.zgraph = zgraph_handle
        else:
            raise ValueError("zgraph_handle must be a ZSpaceGraph instance")

    def is_valid(self):
        """Check if the graph is valid."""
        return self.zgraph.is_valid()

    def get_vertex_count(self):
        """Get the number of vertices in the graph."""
        return self.zgraph.get_vertex_count()

    def get_edge_count(self):
        """Get the number of edges in the graph."""
        return self.zgraph.get_edge_count()

    def create_graph(self, vertex_positions, edge_connections):
        """Create a graph from vertex positions and edge connections."""
        return self.zgraph.create_graph(vertex_positions, edge_connections)

    def get_graph_data(self):
        """Get the graph data as (vertices, edges) tuple."""
        return self.zgraph.get_graph_data()

    def set_vertex_positions(self, vertex_positions):
        """Set the vertex positions of the graph."""
        return self.zgraph.set_vertex_positions(vertex_positions)

    def merge_vertices(self, tolerance):
        """Merge vertices within the given tolerance."""
        return self.zgraph.merge_vertices(tolerance)

    def separate_graph(self):
        """Separate the graph into connected components."""
        return self.zgraph.separate_graph()

    def set_handle(self, handle):
        """Set the internal handle."""
        return self.zgraph.set_handle(handle)

    def get_handle(self):
        """Get the internal handle."""
        return self.zgraph.get_handle()

    def from_compas_network(self, compas_network):
        """Create zSpace graph from COMPAS Network."""
        if not compas_network or compas_network.number_of_nodes() == 0:
            return self
        
        # Extract vertices and edges from COMPAS Network
        vertices = []
        edges = []
        
        # Get vertex positions
        for node in compas_network.nodes():
            # Use node_attributes method which works correctly
            attrs = compas_network.node_attributes(node, ['x', 'y', 'z'])
            x, y, z = attrs[0], attrs[1], attrs[2]
            vertices.extend([x, y, z])
        
        # Get edge connections
        for edge in compas_network.edges():
            u, v = edge
            edges.extend([u, v])
        
        # Convert to numpy arrays
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)
        
        # Create the graph using the wrapper method
        success = self.create_graph(vertices_array, edges_array)
        if not success:
            raise Exception("Failed to create zSpace graph from COMPAS Network")
        
        return self

    def to_compas_network(self):
        """Convert zSpace graph to COMPAS Network datastructure."""
        print("zGraph.to_compas_network: converting zSpace graph to COMPAS Network")
        vertices_array, edges_array = self.zgraph.get_graph_data()
        print("zGraph.to_compas_network: retrieved", len(vertices_array)//3, "vertices and", len(edges_array)//2, "edges")
        vertices = vertices_array.tolist()
        edges = edges_array.tolist()
        
        if len(vertices) == 0:
            return Network()
        
        # Create COMPAS Network
        network = Network()
        
        # Add vertices
        for i, vertex_coords in enumerate(vertices):
            point = Point(*vertex_coords)
            network.add_node(i, x=point.x, y=point.y, z=point.z)
        
        # Add edges
        for j in range(0, len(edges), 2):
            if j + 1 < len(edges):
                start_idx = edges[j]
                end_idx = edges[j + 1]
                if (start_idx >= 0 and end_idx >= 0 and 
                    start_idx < len(vertices) and end_idx < len(vertices)):
                    network.add_edge(start_idx, end_idx)
        
        return network

    def transform(self, tMatrix):
        """Transform the graph vertices using a transformation matrix.
        
        Parameters
        ----------
        tMatrix : list or numpy.ndarray
            4x4 transformation matrix. Can be in row-major or column-major format.
            If using zUtils.plane_to_plane_correct(), will be automatically converted.
            
        Returns
        -------
        bool
            True if transformation was successful, False otherwise
        """
        # Convert tMatrix to numpy array if it's a list
        if isinstance(tMatrix, list):
            tMatrix = np.array(tMatrix, dtype=np.float32)
        elif tMatrix.dtype != np.float32:
            tMatrix = tMatrix.astype(np.float32)
        
        # Ensure matrix is 4x4
        if tMatrix.shape != (4, 4):
            if tMatrix.size == 16:
                tMatrix = tMatrix.reshape(4, 4)
            else:
                return False
        
        # Check if this looks like a correct row-major matrix that needs conversion
        # A correct transformation matrix has translation in the last column [0-2][3]
        # The transposed (incorrect) version has translation in the last row [3][0-2]
        has_translation_in_column = abs(tMatrix[0, 3]) > 1e-6 or abs(tMatrix[1, 3]) > 1e-6 or abs(tMatrix[2, 3]) > 1e-6
        has_translation_in_row = abs(tMatrix[3, 0]) > 1e-6 or abs(tMatrix[3, 1]) > 1e-6 or abs(tMatrix[3, 2]) > 1e-6
        
        if has_translation_in_column and not has_translation_in_row:
            # This is a correct row-major matrix, convert to column-major for C++
            tMatrix = tMatrix.T
            print("zGraph.transform: Converted row-major matrix to column-major for C++ compatibility")
        elif has_translation_in_row and not has_translation_in_column:
            # This is already in the format C++ expects (transposed/column-major-like)
            print("zGraph.transform: Using matrix as-is (legacy transposed format)")
        else:
            print("zGraph.transform: Warning - ambiguous matrix format, using as-is")
            
        # Flatten for C++ binding
        tMatrix = tMatrix.flatten()
        
        # Call C++ transform method
        return self.zgraph.transform(tMatrix)

    def interpolate(self, other_graph, t):
        """Interpolate between this graph and another graph using linear interpolation (lerp).
        
        Checks if both graphs have the same topology (same number of vertices and edges 
        with the same connectivity) before performing interpolation.
        
        Parameters
        ----------
        other_graph : zGraph
            The target graph to interpolate towards
        t : float
            Interpolation parameter in range [0, 1]
            - t=0 returns a copy of this graph
            - t=1 returns a copy of the other_graph
            - t=0.5 returns the midpoint between the two graphs
            
        Returns
        -------
        zGraph
            A new interpolated graph with the same topology as both input graphs
            
        Raises
        ------
        ValueError
            If the graphs don't have the same topology (vertex/edge count mismatch
            or different edge connectivity)
        """
        # Validate input parameter
        if not isinstance(other_graph, zGraph):
            raise ValueError("other_graph must be a zGraph instance")
        
        t = float(t)
        if t < 0.0 or t > 1.0:
            raise ValueError("t must be in range [0, 1]")
        
        # Get graph data from both graphs
        self_vertices, self_edges = self.get_graph_data()
        other_vertices, other_edges = other_graph.get_graph_data()
        
        # Check vertex count
        if len(self_vertices) != len(other_vertices):
            raise ValueError(
                f"Graphs have different vertex counts: {len(self_vertices)} vs {len(other_vertices)}"
            )
        
        # Check edge count
        if len(self_edges) != len(other_edges):
            raise ValueError(
                f"Graphs have different edge counts: {len(self_edges)} vs {len(other_edges)}"
            )
        
        # Check edge connectivity - must have same edges in same order
        if not np.array_equal(self_edges, other_edges):
            raise ValueError(
                "Graphs have different topology (edge connectivity mismatch)"
            )
        
        # Perform linear interpolation of vertex positions
        # Reshape vertices to (n_vertices, 3) for easier interpolation
        n_vertices = len(self_vertices) // 3
        
        self_verts_3d = self_vertices.reshape(-1, 3)
        other_verts_3d = other_vertices.reshape(-1, 3)
        
        # Interpolate: result = self + t * (other - self)
        interpolated_verts_3d = self_verts_3d + t * (other_verts_3d - self_verts_3d)
        
        # Flatten back to original format
        interpolated_vertices = interpolated_verts_3d.flatten()
        
        # Create new graph with interpolated vertices
        result_graph = zGraph()
        success = result_graph.create_graph(interpolated_vertices, self_edges)
        
        if not success:
            raise Exception("Failed to create interpolated graph")
        
        return result_graph

    def project_to_plane(self, plane):
        """Project all graph vertices onto a plane.
        
        Projects each vertex orthogonally onto the specified plane.
        
        Parameters
        ----------
        plane : compas.geometry.Frame or compas.geometry.Plane
            The plane to project vertices onto. Can be either a Frame or Plane object.
            If Frame: uses the frame's point and zaxis (normal)
            If Plane: uses the plane's point and normal
            
        Returns
        -------
        zGraph
            A new graph with vertices projected onto the plane, maintaining the same topology
        """
        # Extract plane properties
        if hasattr(plane, 'point') and hasattr(plane, 'zaxis'):
            # It's a Frame
            plane_point = np.array([plane.point.x, plane.point.y, plane.point.z])
            plane_normal = np.array([plane.zaxis.x, plane.zaxis.y, plane.zaxis.z])
        elif hasattr(plane, 'point') and hasattr(plane, 'normal'):
            # It's a Plane
            plane_point = np.array([plane.point.x, plane.point.y, plane.point.z])
            plane_normal = np.array([plane.normal.x, plane.normal.y, plane.normal.z])
        else:
            raise ValueError("plane must be a Frame or Plane object with point and normal/zaxis attributes")
        
        # Normalize the plane normal
        plane_normal = plane_normal / np.linalg.norm(plane_normal)
        
        # Get graph data
        vertices, edges = self.get_graph_data()
        
        # Reshape vertices to (n_vertices, 3)
        vertices_3d = vertices.reshape(-1, 3)
        
        # Project each vertex onto the plane
        # Formula: projected_point = point - ((point - plane_point) · normal) * normal
        projected_vertices = []
        for vertex in vertices_3d:
            vertex_array = np.array(vertex)
            # Vector from plane point to vertex
            to_vertex = vertex_array - plane_point
            # Distance from plane (signed)
            distance = np.dot(to_vertex, plane_normal)
            # Project onto plane
            projected_vertex = vertex_array - distance * plane_normal
            projected_vertices.append(projected_vertex)
        
        projected_vertices_3d = np.array(projected_vertices)
        projected_vertices_flat = projected_vertices_3d.flatten()
        
        # Create new graph with projected vertices
        result_graph = zGraph()
        success = result_graph.create_graph(projected_vertices_flat, edges)
        
        if not success:
            raise Exception("Failed to create projected graph")
        
        return result_graph

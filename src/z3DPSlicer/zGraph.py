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
            x = compas_network.node_attribute(node, 'x', 0.0)
            y = compas_network.node_attribute(node, 'y', 0.0)
            z = compas_network.node_attribute(node, 'z', 0.0)
            vertices.extend([x, y, z])
        
        # Get edge connections
        for edge in compas_network.edges():
            u, v = edge
            edges.extend([u, v])
        
        # Convert to numpy arrays
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)
        
        # Create the graph
        success = self.zgraph.create_graph(vertices_array, edges_array)
        if not success:
            raise Exception("Failed to create zSpace graph from COMPAS Network")
        
        return self

    def to_compas_network(self):
        """Convert zSpace graph to COMPAS Network datastructure."""
        vertices_array, edges_array = self.zgraph.get_graph_data()
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
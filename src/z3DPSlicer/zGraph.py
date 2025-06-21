from z3DPSlicer._zspace import Graph as ZSpaceGraph
from compas.geometry import Point, Line
from compas.datastructures import Network

class zGraph:
    def __init__(self, zgraph_handle):
        if isinstance(zgraph_handle, ZSpaceGraph):
            self.zgraph = zgraph_handle
        else:
            raise ValueError("zgraph_handle must be a ZSpaceGraph instance")

    def to_compas_lines(self):
        vertices_array, edges_array = self.zgraph.get_graph_data()
        vertices = vertices_array.tolist()
        edges = edges_array.tolist()
        if len(vertices) == 0 or len(edges) == 0:
            return []
        points = [Point(*vertex) for vertex in vertices]
        edge_pairs = []
        for j in range(0, len(edges), 2):
            if j + 1 < len(edges):
                edge_pairs.append([edges[j], edges[j + 1]])
        lines = []
        for edge in edge_pairs:
            if len(edge) == 2:
                start_idx, end_idx = edge
                if (start_idx >= 0 and end_idx >= 0 and start_idx < len(points) and end_idx < len(points)):
                    lines.append(Line(points[start_idx], points[end_idx]))
        return lines

    def to_compas_network(self):
        """Convert zSpace graph to COMPAS Network."""
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
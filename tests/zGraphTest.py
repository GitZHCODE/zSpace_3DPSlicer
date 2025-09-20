
from z3DPSlicer import zMesh, zGraph  
import numpy as np
min_bb = [-2.0, -2.0, 0.0]
max_bb = [2.0, 2.0, 0.0]  
vertices = []
edges = []
 
vertices.extend([0.0, -0.5, 0.0])  # Add the middle vertex [0, 0, 0]

vertices.extend([2.0, -0.5, 0.0])  #
edges.extend([0, 1])  # Define edges by vertex indices


# Convert to numpy arrays as required by create_graph
vertices_array = np.array(vertices, dtype=np.float64)
edges_array = np.array(edges, dtype=np.int32)

graph = zGraph()
print(f"  Vertices array : {vertices_array}")
print(f"  Edges array : {edges_array}")
graph.create_graph(vertices_array, edges_array)
print (f"  Vertex count: {graph.get_vertex_count()}")

vc = graph.get_vertex_count()
print(f"  Vertex count: {vc}")
bc = graph.get_edge_count()
print(f"  Edge count: {bc}")
print(f"  Graph data1143: ")

bd, aa = graph.get_graph_data()
print(bd,aa)


print(f"  Graph data1133: ")
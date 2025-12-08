
from z3DPSlicer import zMesh, zGraph
import numpy as np
import math

# Test with a closed loop polyline of 100 points
min_bb = [-2.0, -2.0, 0.0]
max_bb = [2.0, 2.0, 0.0]
vertices = []
edges = []

# Create 100 points in a circle
radius = 1.0
num_points = 100
for i in range(num_points):
    angle = 2 * math.pi * i / num_points
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    z = 0.0
    vertices.extend([x, y, z])

# Create edges for closed loop
for i in range(num_points):
    edges.extend([i, (i + 1) % num_points])

# Convert to numpy arrays as required by create_graph
vertices_array = np.array(vertices, dtype=np.float64)
edges_array = np.array(edges, dtype=np.int32)

print(f"Created {num_points} vertices in a circle")
print(f"Created {len(edges)//2} edges for closed loop")
print(f"First 10 vertices: {vertices_array[:30]}")  # Show first 10 points (3 coords each)
print(f"First 20 edges: {edges_array[:20]}")  # Show first 20 edge indices

graph = zGraph()
success = graph.create_graph(vertices_array, edges_array)
print(f"Graph creation success: {success}")

vc = graph.get_vertex_count()
print(f"Vertex count: {vc}")

ec = graph.get_edge_count()
print(f"Edge count: {ec}")

print("Getting graph data...")
bd, aa = graph.get_graph_data()
print(f"Vertices data (first 30 values): {bd[:30] if len(bd) > 30 else bd}")
print(f"Edges data (first 20 values): {aa[:20] if len(aa) > 20 else aa}")

# Verify it's a closed loop by checking if first and last vertices are connected
if len(aa) >= 2:
    last_edge = [aa[-2], aa[-1]]
    print(f"Last edge connects vertices: {last_edge}")
    print(f"This should connect vertex {num_points-1} back to vertex 0: {last_edge == [num_points-1, 0]}")
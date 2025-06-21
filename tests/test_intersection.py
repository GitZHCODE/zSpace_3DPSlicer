#!/usr/bin/env python3
"""
Example demonstrating mesh-plane intersection using zSpace.
"""

import numpy as np
from z3DPSlicer import zMesh, zGraph
from compas.datastructures import Mesh as CompasMesh, Network

def main():
    # Create a simple mesh (you can replace this with your own mesh loading)
    mesh = zMesh()
    
    # --- Cube mesh intersection test (matching C# test) ---
    cube_vertices = [
        [-1.0, -1.0, -1.0],  # 0
        [ 1.0, -1.0, -1.0],  # 1
        [ 1.0,  1.0, -1.0],  # 2
        [-1.0,  1.0, -1.0],  # 3
        [-1.0, -1.0,  1.0],  # 4
        [ 1.0, -1.0,  1.0],  # 5
        [ 1.0,  1.0,  1.0],  # 6
        [-1.0,  1.0,  1.0],  # 7
    ]
    cube_faces = [
        [0, 1, 2], [0, 2, 3],      # Front
        [4, 6, 5], [4, 7, 6],      # Back
        [0, 3, 7], [0, 7, 4],      # Left
        [1, 5, 6], [1, 6, 2],      # Right
        [0, 4, 5], [0, 5, 1],      # Bottom
        [2, 6, 7], [2, 7, 3],      # Top
    ]
    compasMesh = CompasMesh.from_vertices_and_faces(cube_vertices, cube_faces)
    compasMesh.quads_to_triangles()
    mesh.from_compas_mesh(compasMesh)

    # Example: Create a simple cube mesh
    # This is a placeholder - you would typically load a mesh from file
    # For demonstration, we'll assume the mesh is created
    
    # Define a plane to intersect with
    # Origin point of the plane
    origin = [0.0, 0.0, 0.0]  # Center of the coordinate system
    
    # Normal vector of the plane (pointing in Z direction)
    normal = [0.0, 0.0, 1.0]  # Z-axis normal
    
    print(f"Intersecting mesh with plane:")
    print(f"  Origin: {origin}")
    print(f"  Normal: {normal}")
    
    # Perform the intersection
    intersection_graph = mesh.intersect_plane(origin, normal)
    
    if intersection_graph is not None:
        print("Intersection successful!")
        
        # Convert to COMPAS Network for visualization
        network = zGraph(intersection_graph).to_compas_network()
        node_count = len(list(network.nodes()))
        edge_count = len(list(network.edges()))
        print(f"Intersection contains {node_count} vertices and {edge_count} edges")
        
    else:
        print("Intersection failed or no intersection found.")
        return None

if __name__ == "__main__":
    main() 
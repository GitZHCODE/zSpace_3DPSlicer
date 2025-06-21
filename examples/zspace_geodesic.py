from compas.geometry import Box, Point, Line
from compas_viewer.viewer import Viewer
from pathlib import Path
from compas.datastructures import Mesh, Network
from compas.colors import Color
from compas.colors.colormap import ColorMap
import numpy as np
from z3DPSlicer import zMesh, zGraph
import time

def main():
    viewer = Viewer()
    mesh = Mesh.from_obj("data/sliceMesh.obj")
    mesh.quads_to_triangles()
    
    try:

        # construct zSpace mesh from compas mesh
        zmesh = zMesh()
        zmesh.from_compas_mesh(mesh)
        print(f"Created zSpace mesh with {zmesh.get_vertex_count()} vertices and {zmesh.get_face_count()} faces")

        # geodesic source vertices
        source_vertices = np.array([100, 800], dtype=np.int32)

        # test 1 - compute geodesic heat
        distances = zmesh.compute_geodesic_heat(source_vertices, normalised=True)
        cmap = ColorMap.from_two_colors(Color.blue(), Color.red())
        min_dist = np.min(distances)
        max_dist = np.max(distances)
        print(f"Distance range: {min_dist:.2f} to {max_dist:.2f}")

        # test 2 - color compas mesh with zSpace geodesic heat
        vertex_colors = {}
        for idx, vertex in enumerate(mesh.vertices()):
            normalized_dist = (distances[idx] - min_dist) / (max_dist - min_dist)
            vertex_colors[vertex] = cmap(normalized_dist)
        viewer.scene.add(mesh, use_vertexcolors=True, pointcolor=vertex_colors, show_lines=False)

        # test 3 - compute geodesic contours as zGraph objects and convert to COMPAS Networks
        time_start = time.time()
        contours, count = zmesh.compute_geodesic_contours(source_vertices, steps=200, dist=0.0)
        time_end = time.time()
        print(f"\n Generated {count} contour graphs in {time_end - time_start:.2f} seconds")
        
        for i in range(count):
            try:
                # separate graph into connected components since compas network does not support multiple components?
                graph = zGraph(contours[i])
                components, component_count = graph.separate_graph()
                for component_graph in components:
                    # Convert Graph object to zGraph object
                    z_component = zGraph(component_graph)
                    network = z_component.to_compas_network()
                    if network.number_of_nodes() > 0:
                        viewer.scene.add(network, linecolor=Color.black(), linewidth=2)
                        print(f"Contour {i}: {network.number_of_nodes()} nodes, {network.number_of_edges()} edges")

                # instead simply do
                '''
                graph = zGraph(contours[i])
                network = graph.to_compas_network()
                if network.number_of_nodes() > 0:
                    viewer.scene.add(network, linecolor=Color.black(), linewidth=2)
                    print(f"Contour {i}: {network.number_of_nodes()} nodes, {network.number_of_edges()} edges")
                '''
            except Exception as e:
                print(f"Failed to process contour {i}: {e}")
                continue

        # visualisation    
        viewer.show()

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

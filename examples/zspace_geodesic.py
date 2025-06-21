from compas.geometry import Box, Point, Line
from compas_viewer.viewer import Viewer
from pathlib import Path
from compas.datastructures import Mesh, Network
from compas.colors import Color
from compas.colors.colormap import ColorMap
import numpy as np
from z3DPSlicer import zMesh, zGraph

def main():
    viewer = Viewer()
    mesh = Mesh.from_obj("data/sliceMesh.obj")

    try:

        # construct zSpace mesh from compas mesh
        zmesh = zMesh(mesh)
        print(f"Created zSpace mesh with {zmesh.get_vertex_count()} vertices and {zmesh.get_face_count()} faces")

        # test 1 - compute geodesic heat
        distances = zmesh.compute_geodesic_heat(0)
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
        contour_graphs = zmesh.compute_geodesic_contours(0, steps=200, dist=0.0)
        print(f"Generated {len(contour_graphs)} contour graphs")
        for i, graph in enumerate(contour_graphs):
            network = graph.to_compas_network()
            if network.number_of_nodes() > 0:  # Only add non-empty networks
                viewer.scene.add(network, linecolor=Color.black(), linewidth=2)
                print(f"Contour {i}: {network.number_of_nodes()} nodes, {network.number_of_edges()} edges")

        # visualisation    
        viewer.show()

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

from compas.geometry import Box, Point, Line
from compas_viewer.viewer import Viewer
from pathlib import Path
from compas.datastructures import Mesh
from compas.colors import Color
from compas.colors.colormap import ColorMap
import numpy as np
from z3DPSlicer import zMesh

def main():
    viewer = Viewer()
    mesh = Mesh.from_obj("data/sliceMesh.obj")
    try:
        zmesh = zMesh(mesh)
        print(f"Created zSpace mesh with {zmesh.get_vertex_count()} vertices and {zmesh.get_face_count()} faces")
        distances = zmesh.compute_geodesic_heat(0)
        cmap = ColorMap.from_two_colors(Color.blue(), Color.red())
        min_dist = np.min(distances)
        max_dist = np.max(distances)
        print(f"Distance range: {min_dist:.2f} to {max_dist:.2f}")
        vertex_colors = {}
        for idx, vertex in enumerate(mesh.vertices()):
            normalized_dist = (distances[idx] - min_dist) / (max_dist - min_dist)
            vertex_colors[vertex] = cmap(normalized_dist)
        viewer.scene.add(mesh, use_vertexcolors=True, pointcolor=vertex_colors, show_lines=False)
        contour_lines = zmesh.compute_geodesic_contours(0, steps=50, dist=0.0)
        print(f"Generated {len(contour_lines)} contour lines")
        for line in contour_lines:
            viewer.scene.add(line, linecolor=Color.black(), linewidth=2)
        viewer.show()
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

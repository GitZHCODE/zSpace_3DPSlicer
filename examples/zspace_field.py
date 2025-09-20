from operator import ne
from compas.geometry import Box, Point, Line
from compas_viewer.viewer import Viewer
from pathlib import Path
from compas.datastructures import Mesh, Network
from compas.colors import Color
from compas.colors.colormap import ColorMap
import numpy as np
from z3DPSlicer import zMesh, zGraph, zField

def main():
    viewer = Viewer()
    mesh = Mesh()
    network = Network()
    
    try:
        # construct zspace field
        min_bb = np.array([0.0, 0.0, 0.0])
        max_bb = np.array([10.0, 10.0, 10.0])
        num_x, num_y = 20, 20
        
        field = zField()
        success = field.create_field(min_bb, max_bb, num_x, num_y)

        # get field mesh as zspace mesh
        zmesh = field.get_mesh()

        # get field values from first circle
        centre1 = np.array([5.0, 5.0, 5.0])
        radius1 = 3.0
        offset1 = 0.5
        values1 = field.get_scalars_circle(centre1, radius1, offset1, False)
        print(f"Field values from first circle: {values1}")

        # get field values from second circle (smaller, offset)
        centre2 = np.array([6.0, 6.0, 5.0])
        radius2 = 1.5
        offset2 = 0.3
        values2 = field.get_scalars_circle(centre2, radius2, offset2, False)
        print(f"Field values from second circle: {values2}")

        # perform boolean subtract: subtract second circle from first circle
        values = field.boolean_subtract(values1, values2, False)
        print(f"Field values after boolean subtract ! (circle1 - circle2): {values}")

        # Set the field values
        field.set_field_values(values)
        field.smooth_field(num_smooth=1)
        values = field.get_field_values()

        # compute field color map based on values
        min_value = np.min(values)
        max_value = np.max(values)
        cmap = ColorMap.from_two_colors(Color.blue(), Color.red())
        vertex_colors = {}
        for idx, value in enumerate(values):
            normalized_value = (value - min_value) / (max_value - min_value)
            vertex_colors[idx] = cmap(normalized_value)

        # convert zspace mesh to compas mesh and color with field values
        mesh = zmesh.to_compas_mesh()
        viewer.scene.add(mesh, use_vertexcolors=True, pointcolor=vertex_colors, show_lines=False)

        # get iso contour from field
        threshold = 0.5
        contour = field.get_iso_contour(threshold)
        
        if contour is not None and contour.get_vertex_count() > 0:
            network = contour.to_compas_network()
            graph = zGraph()    
            graph.from_compas_network(network)
            print(f"Iso contour vertex count: {contour.get_graph_data()}")
            if network.number_of_nodes() > 0:
                viewer.scene.add(network, linecolor=Color.black(), linewidth=2)

        # visualisation  
        viewer.show()

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()

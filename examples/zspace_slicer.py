from os import name
import compas
from compas_viewer import Viewer
from compas.geometry import Point, Frame, Vector
from compas.datastructures import Mesh, Network

import numpy as np
import json
from compas.colors import Color
from compas.colors.colormap import ColorMap
from z3DPSlicer import zGraph, zSlicer, zUtils


def read_mesh_from_zJSON(filePath):
    """Load mesh data from a JSON created by zSpace and update self.mesh.
    
    Parameters
    ----------
    filePath : str
        Path to the JSON file created by zSpace.
    """

    # Load the JSON data
    with open(filePath, 'r') as file:
        data = json.load(file)
    
    print(f"Loaded JSON data from: {filePath}")
    
    # Extract vertex positions from VertexAttributes
    vertices = []
    if "VertexAttributes" in data:
        for attr_list in data["VertexAttributes"]:
            # Each vertex has x,y,z at the beginning (based on C++ code)
            # Different formats might have 3, 6, 9 or 15 values per vertex
            if len(attr_list) >= 3:
                x, y, z = attr_list[0:3]
                vertices.append([x, y, z])
    
    # If no vertices were found in VertexAttributes, try another approach
    if not vertices and "Vertices" in data:
        # This is a fallback, exact structure depends on how zSpace stores mesh data
        print("Using fallback vertex loading method")
        vertices = data["Vertices"]
        
    # Extract faces from the JSON
    faces = []
    if "Faces" in data and "Halfedges" in data:
        # Need to reconstruct faces from half-edge structure
        face_start_halfedges = data["Faces"]
        halfedges = data["Halfedges"]
        
        for face_he_idx in face_start_halfedges:
            if face_he_idx == -1:
                continue
                
            face_vertices = []
            current_he_idx = face_he_idx
            
            # Follow halfedges to build the face loop
            while True:
                # Get vertex from halfedge
                if current_he_idx >= 0 and current_he_idx < len(halfedges):
                    halfedge = halfedges[current_he_idx]
                    if len(halfedge) > 2:  # Ensure halfedge has vertex info
                        vertex_idx = halfedge[2]  # Based on C++ code, vertex index is at position 2
                        face_vertices.append(vertex_idx)
                    
                    # Move to next halfedge in the face
                    current_he_idx = halfedge[1]  # Next halfedge index
                    
                    # Break if we've looped back to start
                    if current_he_idx == face_he_idx:
                        break
                else:
                    break
            
            if len(face_vertices) >= 3:
                faces.append(face_vertices)
    
    # As a fallback, check if there's a more direct representation of faces
    if not faces and "FaceIndices" in data:
        faces = data["FaceIndices"]
    
    # Update self.mesh from vertices and faces
    if vertices and faces:
        print(f"Updating mesh with {len(vertices)} vertices and {len(faces)} faces")
        return Mesh.from_vertices_and_faces(vertices, faces)
    else:
        print(f"Warning: Could not extract vertices and faces from JSON data")
        print(f"Vertices found: {len(vertices)}, Faces found: {len(faces)}")
        return Mesh()

def read_start_end_planes(filePath):
    """Load start and end planes from a JSON created by zSpace.
    
    Parameters
    ----------
    filePath : str
        Path to the JSON file created by zSpace.
    
    Returns
    -------
    tuple
        A tuple containing (startPlane, endPlane) or (None, None) if not found
    """
    startPlane = None
    endPlane = None

    with open(filePath, 'r') as file:
        data = json.load(file)
    
    if "LeftPlanes" in data:
        ###plane location in viewer is in correct for some reason, using frmae instead
        if len(data["LeftPlanes"]) == 2:
            start_planes_data = data["LeftPlanes"][0]
            # print(f"Start plane data: {start_planes_data}")
            basePt_start = Point(start_planes_data[3], start_planes_data[7], start_planes_data[11])
            normal_start_0 = Vector(start_planes_data[0], start_planes_data[4], start_planes_data[8])
            normal_start_1 = Vector(start_planes_data[1], start_planes_data[5], start_planes_data[9])
            startPlane = Frame(basePt_start, normal_start_0, normal_start_1)

            end_planes_data = data["LeftPlanes"][1]
            # print(f"End plane data: {end_planes_data}")
            basePt_end = Point(end_planes_data[3], end_planes_data[7], end_planes_data[11])
            normal_end_0 = Vector(end_planes_data[0], end_planes_data[4], end_planes_data[8])
            normal_end_1 = Vector(end_planes_data[1], end_planes_data[5], end_planes_data[9])
            endPlane = Frame(basePt_end, normal_end_0, normal_end_1)

            return startPlane, endPlane
        else:
            print("Warning: LeftPlanes does not contain exactly two planes.")
            return None, None
    else:
        print("Warning: LeftPlanes not found in JSON data.")
        return None, None


# Load mesh and planes from JSON
local_path = "C:\\Users\\Wo.Lin\\source\\repos\\zSpace_3DPSlicer\\data\\blockMesh_23.json"
mesh = read_mesh_from_zJSON(local_path)
startPlane, endPlane = read_start_end_planes(local_path)

# Create slicer and perform slicing
slicer = zSlicer()
slicer.min_bb = [-0.5,-1.5, 0.0]
slicer.max_bb = [0.5, 0.5, 0.0]
slicer.set_mesh(mesh)

# init field
slicer.init_field(256, 256)  # Initialize field resolution

# Define print parameters
print_height = 0.0060  # Number of layers desired
# print_height = 0.10  # Number of layers desired

print_width = 0.014  # Width of the print path

slicer.slice(startPlane, endPlane, print_height, start_plane_offset=0.005, end_plane_offset=0.005)

# Update all contours at once
slicer.update_all_contours(print_width)

print(f"Total contours: {len(slicer.contours)}")
print(f"Total fields: {len(slicer.fields)}")

#export contours to JSON
output_path = "./data/blockMesh_23_contours.json"
slicer.export_contours(output_path, print_width, print_height=print_height)
print(f"Exported contours to: {output_path}")
# Initialize viewer
viewer = Viewer()

# Add mesh with low opacity
viewer.scene.add(mesh, linecolor=Color.grey(), linewidth=1, show_lines=False, opacity=0.5,name="Input")
print("mesh added")

# Add all contours to the scene
for i, contour in enumerate(slicer.contours):
    if contour is not None:
        try:
            network = contour.to_compas_network()
            if network.number_of_nodes() > 0:
                viewer.scene.add(network, linecolor=Color.magenta(), linewidth=2, name=f"Contour {i}")
                print(f"Added contour for layer {i}")
        except Exception as e:
            print(f"Error adding contour for layer {i}: {e}")

# Add center points visualization
print(f"Adding center points for {len(slicer.centers)} layers")
for i, center in enumerate(slicer.centers):
    if center is not None and len(center) >= 3:
        try:
            center_point = Point(center[0], center[1], center[2])
            viewer.scene.add(center_point, pointcolor=Color.red(), pointsize=10, name=f"Center {i}")
            print(f"Added center point for layer {i}: {center}")
        except Exception as e:
            print(f"Error adding center point for layer {i}: {e}")

# Add first points of contours visualization
print(f"Adding first contour points for visualization")
for i, contour in enumerate(slicer.contours):
    if contour is not None:
        try:
            network = contour.to_compas_network()
            if network.number_of_nodes() > 0:
                # Get the first node in the network
                first_node = list(network.nodes())[0]
                node_coords = network.node_coordinates(first_node)
                first_point = Point(node_coords[0], node_coords[1], node_coords[2])
                viewer.scene.add(first_point, pointcolor=Color.green(), pointsize=8, name=f"Seam {i}")
                print(f"Added first point for layer {i}: {node_coords}")
        except Exception as e:
            print(f"Error adding first point for layer {i}: {e}")

# Add only the first valid field mesh (layer 1, since we skip boundary layer 0)
target_layer = 1
if target_layer < len(slicer.fields):
    field = slicer.fields[target_layer]
    if field is not None:
        try:
            field_mesh = field.get_mesh().to_compas_mesh()
            
            # Get field values and create color mapping
            values = field.get_field_values()
            contours = field.get_iso_contour_direct(0)
            if values is not None and len(values) > 0:
                values = np.array(values)
                min_value = np.min(values)
                max_value = np.max(values)
                
                if max_value > min_value:  # Avoid division by zero
                    cmap = ColorMap.from_two_colors(Color.blue(), Color.red())
                    vertex_colors = {}
                    for idx, value in enumerate(values):
                        normalized_value = (value - min_value) / (max_value - min_value)
                        vertex_colors[idx] = cmap(normalized_value)
                    
                    # Add field mesh to scene
                    viewer.scene.add(field_mesh, use_vertexcolors=True, pointcolor=vertex_colors, show_lines=False,name= f"SDF Mesh {target_layer}")
                    print(f"Added field mesh for layer {target_layer}")
                    
                    # Add iso contour if available

                    viewer.scene.add(contours.to_compas_network(), linecolor=Color.magenta(), linewidth=3)

                        
        except Exception as e:
            print(f"Error adding field for layer {target_layer}: {e}")

print(f"\nVisualization complete!")
print(f"Showing:")
print(f"- Original mesh (transparent)")
print(f"- All contours ({len([c for c in slicer.contours if c is not None])} layers)")
print(f"- Center points for each layer (red points)")
print(f"- First points of each contour (green points)")
print(f"- Field mesh for layer {target_layer}")


viewer.show()


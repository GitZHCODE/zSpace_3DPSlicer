from os import name
import compas
from compas_viewer import Viewer
from compas.geometry import Point, Frame, Vector, Transformation
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


def transform_mesh_to_worldxy(mesh, start_plane):
    """Transform mesh to align with world XY plane based on start plane orientation.
    Uses the CORRECT transformation (without the transpose bug) for COMPAS meshes.
    
    Parameters
    ----------
    mesh : compas.datastructures.Mesh
        The mesh to transform
    start_plane : compas.geometry.Frame
        The start plane frame to use as reference (should be the first slicing frame)
        
    Returns
    -------
    compas.datastructures.Mesh
        The transformed mesh
    """
    if start_plane is None:
        print("Warning: No start plane provided, returning original mesh")
        return mesh
    
    # Use the CORRECT transformation for COMPAS meshes (without the transpose bug)
    # This provides the mathematically correct transformation for mesh display
    first_transform = zUtils.plane_to_plane_correct(start_plane, Frame.worldXY())
    
    # COMPAS expects the transformation matrix as a list of lists
    if isinstance(first_transform, np.ndarray):
        first_transform = first_transform.tolist()
    
    # Create a copy of the mesh to transform
    mesh_transformed = mesh.copy()
    
    # Apply the correct transformation for proper mesh alignment
    mesh_transformed.transform(first_transform)

    print(f"Transformed mesh using CORRECT transformation (without transpose bug)")
    print(f"Start plane origin: {start_plane.point}")
    print(f"Start plane X-axis: {start_plane.xaxis}")  
    print(f"Start plane Y-axis: {start_plane.yaxis}")
    print(f"Start plane Z-axis: {start_plane.zaxis}")
    print(f"Using plane_to_plane_correct for proper mesh alignment")
    
    return mesh_transformed


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
slicer.init_field(400, 400)  # Initialize field resolution

# Define print parameters
# print_height = 0.012  # Number of layers desired
print_height = 0.6  # Number of layers desired

print_width = 0.028  # Width of the print path

slicer.slice(startPlane, endPlane, print_height, start_plane_offset=0.005, end_plane_offset=0.005)

# Update all contours at once
slicer.update_all_contours(print_width,shape="Y")

print(f"Total contours: {len(slicer.contours)}")
print(f"Total fields: {len(slicer.fields)}")

#export contours to JSON
output_path = "./data/blockMesh_23_contours.json"
slicer.export_contours(output_path, print_width, print_height=print_height)
print(f"Exported contours to: {output_path}")
# Initialize viewer
viewer = Viewer()

# Get the first slicing frame to match the slicer's first_transform
slicer_frames = slicer.get_frames()
if slicer_frames and len(slicer_frames) > 0:
    first_slicing_frame = slicer_frames[0]
    print(f"Using first slicing frame for mesh transformation:")
    print(f"  Origin: {first_slicing_frame.point}")
    print(f"  X-axis: {first_slicing_frame.xaxis}")
    print(f"  Y-axis: {first_slicing_frame.yaxis}")
    print(f"  Z-axis: {first_slicing_frame.zaxis}")
    
    # Transform mesh to match the slicer's coordinate system
    mesh = transform_mesh_to_worldxy(mesh, first_slicing_frame)
else:
    print("Warning: No slicing frames found, using original startPlane for transformation")
    mesh = transform_mesh_to_worldxy(mesh, startPlane)

viewer.scene.add(mesh, linecolor=Color.grey(), linewidth=1, show_lines=False, opacity=0.1,name="Input")
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
target_layer = 0
if target_layer < len(slicer.fields):
    field = slicer.fields[target_layer]
    if field is not None:
        try:
            field_mesh = field.get_mesh().to_compas_mesh()
            
            # Get field values and create color mapping
            contours = slicer.polygon_contours[target_layer]
            values = field.get_field_values()

            if values is not None and len(values) > 0:
                values = np.array(values)
                
                # Create color mapping based on field values
                threshold = 0.02
                vertex_colors = {}
                for idx, value in enumerate(values):
                    if value > threshold:
                        vertex_colors[idx] = Color.from_rgb255(220, 220, 220)
                    elif value < -threshold:
                        # Map value from -1.0 to -threshold into color from (0,40,240) to (180,200,255)
                        t = min(max((value + 1.0) / (1.0 - threshold), 0.0), 1.0)  # Clamp t between 0 and 1
                        r = int(0 + t * (180 - 0))
                        g = int(40 + t * (200 - 40))
                        b = int(240 + t * (255 - 240))
                        vertex_colors[idx] = Color.from_rgb255(r, g, b)
                    else:  # Between -threshold and threshold
                        vertex_colors[idx] = Color.from_rgb255(240, 0, 140)
                # Add field mesh to scene
                viewer.scene.add(field_mesh, use_vertexcolors=True, pointcolor=vertex_colors, show_lines=False,name= f"SDF Mesh {target_layer}")
                print(f"Added field mesh for layer {target_layer}")
                
                # Add iso contour if available
                viewer.scene.add(contours.to_compas_network(), linecolor=Color.black(), linewidth=6,name= f"Mesh_Contour_{target_layer}")                        
        except Exception as e:
            print(f"Error adding field for layer {target_layer}: {e}")

# min_sdf_bb_point = Point(*slicer.min_SDF_bb[target_layer])
# max_sdf_bb_point = Point(*slicer.max_SDF_bb[target_layer])
# viewer.scene.add(min_sdf_bb_point, pointcolor=Color.red(), pointsize=12, name=f"Min SDF BB {target_layer}")
# viewer.scene.add(max_sdf_bb_point, pointcolor=Color.red(), pointsize=12, name=f"Max SDF BB {target_layer}")

print(f"\nVisualization complete!")
print(f"Showing:")
print(f"- Original mesh (transparent)")
print(f"- All contours ({len([c for c in slicer.contours if c is not None])} layers)")
print(f"- Center points for each layer (red points)")
print(f"- First points of each contour (green points)")
print(f"- Field mesh for layer {target_layer}")

# Set camera position and target
# Position the camera at a specific location [x, y, z]
camera_position = [2.0, -3.0, 2.5]  # Adjust these values as needed
camera_target = [0.0, 0.0, 0.0]     # Point the camera is looking at

# Configure the camera before showing the viewer
viewer.renderer.camera.position.set(camera_position[0], camera_position[1], camera_position[2])
viewer.renderer.camera.target.set(camera_target[0], camera_target[1], camera_target[2])


# Remove the grid
viewer.config.renderer.show_grid = False

viewer.show()


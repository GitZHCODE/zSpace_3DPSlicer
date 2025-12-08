from os import name
from tracemalloc import start
import compas
import os
from compas_viewer import Viewer
from compas_viewer.events import KeyEvent
from compas.geometry import Point, Frame, Vector, Transformation
from compas.datastructures import Mesh, Network
from PySide6.QtWidgets import QSlider, QLabel, QVBoxLayout, QWidget, QDockWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import numpy as np
import json
from compas.colors import Color
from compas.colors.colormap import ColorMap
from z3DPSlicer import zGraph, zSlicer, zUtils
from compas.geometry import Translation


###########GLOBAL VARIABLES
# Initialize viewer
viewer = Viewer()
mesh = None
startPlane = None
endPlane = None
slicer = zSlicer()
slicer.min_bb = [-1.5,-0.5, 0.0]
slicer.max_bb = [1, 1, 0.0]
slicer.init_field(200, 200) # Initialize field resolution
print_height = 0.6  # Number of layers desired
print_width = 0.028  # Width of the print path
is_original_position = True
bracing_type = "Y"
load_mesh_path=r"\\zaha-hadid.com\Data\Projects\1453_CODE\1453___research\res_linwo\4359_mocaup\25251208\blockMesh.obj"
load_planes_path=r"\\zaha-hadid.com\Data\Projects\1453_CODE\1453___research\res_linwo\4359_mocaup\25251208\plane.json"
output_path = "./data/blockMesh_4_carb_contours.json"



##############viewer config
# Remove the grid
# viewer.config.renderer.show_grid = False
## Set application name and icon
viewer.app.setApplicationDisplayName("zSpace_COMPAS viewer")
viewer.app.setApplicationName("zSpace_COMPAS viewer")
viewer.ui.window.widget.setWindowTitle("zSpace_COMPAS viewer")
script_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(script_dir, "..", "documentation", "Assets", "zspaceIcon.png")
viewer.app.setWindowIcon(QIcon(icon_path))

# Configure an orthographic top view so the scene renders from above
# viewer.config.renderer.view = "top"
# viewer.renderer.view = "top"
# viewer.renderer.camera.reset_position(view="top")
# viewer.renderer.camera.target.set(0.0, -0.5, 0.0)
# viewer.renderer.camera.distance = 2.0  # Controls orthographic zoom extent

###########################utils

def _reset_buffer_manager_buffers(buffer_manager):
    """Reinitialize viewer buffer manager arrays after manual clears."""
    data_types = ["_points_data", "_lines_data", "_frontfaces_data", "_backfaces_data"]
    for data_type in data_types:
        buffer_manager.positions[data_type] = np.array([], dtype=np.float32)
        buffer_manager.colors[data_type] = np.array([], dtype=np.float32)
        buffer_manager.elements[data_type] = np.array([], dtype=np.int32)
        if data_type in ("_frontfaces_data", "_backfaces_data"):
            buffer_manager.elements[data_type + "_transparent"] = np.array([], dtype=np.int32)
        buffer_manager.object_indices[data_type] = np.array([], dtype=np.float32)
        # buffer_manager.buffer_ids[data_type] = {}

def read_mesh_from_obj(filePath):
    """Load mesh data from a JSON created by zSpace and update self.mesh.
    
    Parameters
    ----------
    filePath : str
        Path to the JSON file created by zSpace.
    """

    # Load the JSON data
    return Mesh.from_obj(filePath)
        

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
    
    if "startPlane" in data and "endPlane" in data:
        try:
            # Parse startPlane
            start_data = data["startPlane"]
            basePt_start = Point(*start_data["origin"])
            normal_start_0 = Vector(*start_data["xaxis"])
            normal_start_1 = Vector(*start_data["yaxis"])
            startPlane = Frame(basePt_start, normal_start_0, normal_start_1)
            
            # Parse endPlane
            end_data = data["endPlane"]
            basePt_end = Point(*end_data["origin"])
            normal_end_0 = Vector(*end_data["xaxis"])
            normal_end_1 = Vector(*end_data["yaxis"])
            endPlane = Frame(basePt_end, normal_end_0, normal_end_1)
            
            return startPlane, endPlane
        except (KeyError, ValueError) as e:
            print(f"Error parsing plane data: {e}")
            return None, None
    else:
        print("Warning: startPlane or endPlane not found in JSON data.")
        return None, None


###sliders

def on_printHeight_slider_change(value):
    """Callback when slider value changes."""
    global print_height
    print_height = value / 1000.0  # Scale to 0.01 - 0.5
    slider_label.setText(f"Print Height: {print_height:.3f}")
    print(f"Slider value changed to: {print_height:.3f}")

def on_bracing_slider_change(value):
    global bracing_type
    if value == 0:
        bracing_type = "line"
    elif value == 1:
        bracing_type = "Y"
    else:
        bracing_type = "diagonal"
    slider_bracing_label.setText(f"Bracing Type: {bracing_type}")
    print(f"Bracing type changed to: {bracing_type}")

# Create a custom widget with slider
slider_widget = QWidget()
slider_layout = QVBoxLayout()

# Create label
slider_label = QLabel(f"Print Height: {print_height:.2f}")
slider_layout.addWidget(slider_label)
# Create label
slider_bracing_label = QLabel(f"Bracing Type: {bracing_type}")
slider_layout.addWidget(slider_bracing_label)
# Create slider (range 10-200, representing 0.01-0.2)
slider = QSlider(Qt.Orientation.Horizontal)
slider.setMinimum(10)
slider.setMaximum(200)
slider.setValue(200)  # Default value 0.2
slider.setTickPosition(QSlider.TickPosition.TicksBelow)
slider.setTickInterval(1)
slider.valueChanged.connect(on_printHeight_slider_change)
slider_layout.addWidget(slider)

# create bracing type
slider_bracing = QSlider(Qt.Orientation.Horizontal)
slider_bracing.setMinimum(0)
slider_bracing.setMaximum(2)
slider_bracing.setValue(0)  # Default value 1
slider_bracing.setTickPosition(QSlider.TickPosition.TicksBelow)
slider_bracing.setTickInterval(1)
slider_bracing.valueChanged.connect(on_bracing_slider_change)

slider_layout.addWidget(slider_bracing)

slider_widget.setLayout(slider_layout)



# Create a dock widget for the slider
dock = QDockWidget("Print Params", viewer.ui.window.widget)
dock.setWidget(slider_widget)
viewer.ui.window.widget.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)

###################keypress event
############KEYTRIGGERED FUNCTION
def on_read_mesh():
    """Load mesh when key is pressed."""
    global mesh, startPlane, endPlane,is_original_position
    is_original_position = True
    #clear scene if not empty
    if len(viewer.scene.objects) > 0:
        # Remove all objects
        for obj in list(viewer.scene.objects):
            viewer.scene.remove(obj)
            print(f"Removing: {obj.name}")
        
        # Clear and rebuild the buffer manager
        viewer.renderer.buffer_manager.clear()
        viewer.renderer.buffer_manager.objects.clear()  # Important: clear the objects dict too
        viewer.renderer.buffer_manager.object_indices.clear()
        _reset_buffer_manager_buffers(viewer.renderer.buffer_manager)
        print("Cleared scene and buffer manager")
    
    # Load mesh and planes from JSON
    mesh = read_mesh_from_obj(load_mesh_path)
    startPlane, endPlane = read_start_end_planes(load_planes_path)
    mObj = viewer.scene.add(mesh, linecolor=Color.grey(), linewidth=1, show_lines=True, opacity=1, name="Input",facecolor=Color.from_rgb255(200,200,200))
    mObj.init()
    viewer.renderer.buffer_manager.add_object(mObj)
    viewer.renderer.buffer_manager.create_buffers()
    viewer.renderer.update()
    viewer.ui.sidebar.update()
    print("mesh added")

def on_computeFrames():
    """Perform slicing when key is pressed."""
    global mesh, startPlane, endPlane, slicer, contour_objects
    if mesh is None or startPlane is None or endPlane is None:
        print("Error: Mesh or planes not loaded. Please load mesh first.")
        return
    

    slicer.set_mesh(mesh)
    slicer.slice(startPlane, endPlane, print_height, start_plane_offset=0.01, end_plane_offset=0.01)
    
    # Batch add all contours first
    contour_objects = []
    for i, contour in enumerate(slicer.polygon_contours):
        if contour is not None:
            try:
                network = contour.to_compas_network()
                if network.number_of_nodes() > 0:
                    contour_obj = viewer.scene.add(network, linecolor=Color.magenta(), linewidth=2, name=f"Contour {i}")
                    contour_obj.init()
                    viewer.renderer.buffer_manager.add_object(contour_obj)
                    contour_objects.append(contour_obj)
                    print(f"Added contour for layer {i}")
            except Exception as e:
                print(f"Error adding contour for layer {i}: {e}")
    
    # ONLY call these ONCE after all objects are added
    viewer.renderer.buffer_manager.create_buffers()
    viewer.renderer.update()
    viewer.ui.sidebar.update()
    
    print(f"Slicing complete: {len(contour_objects)} contours added")

def on_transform():
    """Transform all objects between original position and world XY."""
    global is_original_position
    
    # Check if we have slicing frames
    slicer_frames = slicer.get_frames()
    if not slicer_frames or len(slicer_frames) == 0:
        first_slicing_frame = startPlane

    else:
        first_slicing_frame = slicer_frames[0]

    
    if len(viewer.scene.objects) == 0:
        print("Error: No objects in scene to transform.")
        return
    

    
    # Decide which transformation to apply based on current state
    if is_original_position:
        # Transform from original position to world XY
        transformation = zUtils.plane_to_plane_correct(first_slicing_frame, Frame.worldXY())
        print("Transforming to World XY position...")
        is_original_position = False
    else:
        # Transform back from world XY to original position
        transformation = zUtils.plane_to_plane_correct(Frame.worldXY(), first_slicing_frame)
        print("Transforming back to Original position...")
        is_original_position = True
    
    # Convert to list format if numpy array
    if isinstance(transformation, np.ndarray):
        transformation = transformation.tolist()
    
    # Clear and rebuild buffer manager
    viewer.renderer.buffer_manager.clear()
    viewer.renderer.buffer_manager.objects.clear()
    viewer.renderer.buffer_manager.object_indices.clear()
    _reset_buffer_manager_buffers(viewer.renderer.buffer_manager)
    
    # Transform all objects and re-add them to buffer manager
    transformed_objects = []
    for obj in viewer.scene.objects:
        # Get the underlying geometry and transform it
        if hasattr(obj, '_item') and obj.name != "Field":
            geometry = obj._item
            if hasattr(geometry, 'transform'):
                geometry.transform(transformation)
                print(f"Transformed object: {obj.name}")
        
        # Re-initialize and add to buffer manager
        obj.init()
        viewer.renderer.buffer_manager.add_object(obj)
        transformed_objects.append(obj)
    
    # Recreate buffers and update display
    viewer.renderer.buffer_manager.create_buffers()
    viewer.renderer.update()
    viewer.ui.sidebar.update()
    
    state = "Original" if is_original_position else "World XY"
    print(f"Transformation complete. Current state: {state}")
    print(f"Transformed {len(transformed_objects)} objects")

def on_compute_SDF():
    """Compute SDF field when key is pressed."""
    global slicer, mesh,is_original_position
    is_original_position = True
    if len(slicer.polygon_contours) == 0:
        print("Error: Not compute frames yet, press p.")
        return
    
    slicer.update_all_contours(print_width,shape=bracing_type,line_number=3)
    print("SDF field computation complete.")
    
    # Remove only contour objects (selective removal)
    
    if len(viewer.scene.objects) > 0:
        # Remove all objects
        for obj in list(viewer.scene.objects):
            viewer.scene.remove(obj)
            print(f"Removing: {obj.name}")
        
        # Clear and rebuild the buffer manager
        viewer.renderer.buffer_manager.clear()
        viewer.renderer.buffer_manager.objects.clear()  # Important: clear the objects dict too
        viewer.renderer.buffer_manager.object_indices.clear()
        _reset_buffer_manager_buffers(viewer.renderer.buffer_manager)
        print("Cleared scene and buffer manager")
   
    # mObj = viewer.scene.add(mesh, linecolor=Color.grey(), linewidth=1, show_lines=True, opacity=0.7, name="Input")
    # mObj.init()
    # viewer.renderer.buffer_manager.add_object(mObj)

    #     # Batch add all contours first
    # SDF_contour_objects = []
    for i, contour in enumerate(slicer.contours):
        if contour is not None:
            try:
                network = contour.to_compas_network()
                if network.number_of_nodes() > 0:
                    contour_obj = viewer.scene.add(network, linecolor=Color.magenta(), linewidth=2, name=f"SDF_Contour {i}")
                    contour_obj.init()
                    viewer.renderer.buffer_manager.add_object(contour_obj)
                    # contour_objects.append(contour_obj)
                    print(f"Added contour for layer {i}")
            except Exception as e:
                print(f"Error adding contour for layer {i}: {e}")
    

    ######field mesh visualization
        target_layer = 0
    if target_layer < len(slicer.fields):
        polygon = slicer.polygon_contours[target_layer]
        field = slicer.fields[target_layer]
        if field is not None:
            field_mesh = field.get_mesh().to_compas_mesh()
            
            # Get field values and create color mapping
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
                fObj = viewer.scene.add(field_mesh,linecolor=Color.from_rgb255(240,240, 240), linewidth=0.1,use_vertexcolors=True, pointcolor=vertex_colors, show_lines=False,name= f"Field")
                fObj.init()
                viewer.renderer.buffer_manager.add_object(fObj)

                polyObj = viewer.scene.add(polygon.to_compas_network(), linecolor=Color.black(), linewidth=6,name= f"Mesh_Contour_{target_layer}")
                polyObj.init()
                viewer.renderer.buffer_manager.add_object(polyObj)
                print(f"Added field mesh for layer {target_layer}")
                
    # ONLY call these ONCE after all objects are added
    mObj = viewer.scene.add(mesh, linecolor=Color.grey(), linewidth=1, show_lines=True, opacity=1, name="Input",facecolor=Color.from_rgb255(200,200,200))
    mObj.init()
    viewer.renderer.buffer_manager.add_object(mObj)
    viewer.renderer.buffer_manager.create_buffers()
    viewer.renderer.update()
    viewer.ui.sidebar.update()

def on_export_contours():
    """Export contours to JSON when key is pressed."""
    global slicer, print_width, output_path, print_height
    if len(slicer.contours) == 0:
        print("Error: No contours to export. Please compute frames first.")
        return
    
    slicer.export_contours(output_path, print_width, print_height=print_height)
    print(f"Exported contours to: {output_path}")

# read mesh
for key in ["r", "R"]:
    add_event = KeyEvent(title="Load Mesh", key=key)
    add_event.triggered.connect(on_read_mesh)
    viewer.eventmanager.key_events.append(add_event)

#compute frames
for key in ["p", "P"]:
    compute_event = KeyEvent(title="Compute Slicing", key=key)
    compute_event.triggered.connect(on_computeFrames)
    viewer.eventmanager.key_events.append(compute_event)

#Transform toggle between original and world XY
for key in ["t", "T"]:
    transform_event = KeyEvent(title="Toggle Transform", key=key)
    transform_event.triggered.connect(on_transform)
    viewer.eventmanager.key_events.append(transform_event)

for key in ["o", "O"]:
    sdf_event = KeyEvent(title="Compute SDF", key=key)
    sdf_event.triggered.connect(on_compute_SDF)
    viewer.eventmanager.key_events.append(sdf_event)

for key in ["e", "E"]:
    export_event = KeyEvent(title="Export Contours", key=key)
    export_event.triggered.connect(on_export_contours)
    viewer.eventmanager.key_events.append(export_event)
#Transform to world xy
def transform_to_world_xy(mesh, slicing_frame):
    # Apply transformation to mesh based on slicing frame
    mesh.apply_transform(slicing_frame.get_transform())
    return mesh


# #####################################fenjiexian
# # Update all contours at once
# slicer.update_all_contours(print_width,shape="diagonal",line_number=1)

# print(f"Total contours: {len(slicer.contours)}")
# print(f"Total fields: {len(slicer.fields)}")

# #export contours to JSON
# output_path = "./data/blockMesh_23_contours.json"
# slicer.export_contours(output_path, print_width, print_height=print_height)
# print(f"Exported contours to: {output_path}")


# # Get the first slicing frame to match the slicer's first_transform
# slicer_frames = slicer.get_frames()
# if slicer_frames and len(slicer_frames) > 0:
#     first_slicing_frame = slicer_frames[0]
#     print(f"Using first slicing frame for mesh transformation:")
#     print(f"  Origin: {first_slicing_frame.point}")
#     print(f"  X-axis: {first_slicing_frame.xaxis}")
#     print(f"  Y-axis: {first_slicing_frame.yaxis}")
#     print(f"  Z-axis: {first_slicing_frame.zaxis}")
    
#     # Transform mesh to match the slicer's coordinate system
#     mesh = transform_mesh_to_worldxy(mesh, first_slicing_frame)
# else:
#     print("Warning: No slicing frames found, using original startPlane for transformation")
#     mesh = transform_mesh_to_worldxy(mesh, startPlane)



# # Add all contours to the scene
# for i, contour in enumerate(slicer.contours):
#     if contour is not None:
#         try:
#             network = contour.to_compas_network()
#             if network.number_of_nodes() > 0:
#                 viewer.scene.add(network, linecolor=Color.magenta(), linewidth=2, name=f"Contour {i}")
#                 print(f"Added contour for layer {i}")
#         except Exception as e:
#             print(f"Error adding contour for layer {i}: {e}")

# # Add first points of contours visualization
# print(f"Adding first contour points for visualization")
# for i, contour in enumerate(slicer.contours):
#     if contour is not None:
#         try:
#             network = contour.to_compas_network()
#             if network.number_of_nodes() > 0:
#                 # Get the first node in the network
#                 first_node = list(network.nodes())[0]
#                 node_coords = network.node_coordinates(first_node)
#                 first_point = Point(node_coords[0], node_coords[1], node_coords[2])
#                 viewer.scene.add(first_point, pointcolor=Color.green(), pointsize=8, name=f"Seam {i}")
#                 print(f"Added first point for layer {i}: {node_coords}")
#         except Exception as e:
#             print(f"Error adding first point for layer {i}: {e}")

# # Add only the first valid field mesh (layer 1, since we skip boundary layer 0)
# target_layer = 0
# if target_layer < len(slicer.fields):
#     field = slicer.fields[target_layer]
#     if field is not None:
#         try:
#             field_mesh = field.get_mesh().to_compas_mesh()
            
#             # Get field values and create color mapping
#             contours = slicer.polygon_contours[target_layer]
#             values = field.get_field_values()

#             if values is not None and len(values) > 0:
#                 values = np.array(values)
                
#                 # Create color mapping based on field values
#                 threshold = 0.02
#                 vertex_colors = {}
#                 for idx, value in enumerate(values):
#                     if value > threshold:
#                         vertex_colors[idx] = Color.from_rgb255(220, 220, 220)
#                     elif value < -threshold:
#                         # Map value from -1.0 to -threshold into color from (0,40,240) to (180,200,255)
#                         t = min(max((value + 1.0) / (1.0 - threshold), 0.0), 1.0)  # Clamp t between 0 and 1
#                         r = int(0 + t * (180 - 0))
#                         g = int(40 + t * (200 - 40))
#                         b = int(240 + t * (255 - 240))
#                         vertex_colors[idx] = Color.from_rgb255(r, g, b)
#                     else:  # Between -threshold and threshold
#                         vertex_colors[idx] = Color.from_rgb255(240, 0, 140)
#                 # Add field mesh to scene
#                 viewer.scene.add(field_mesh, use_vertexcolors=True, pointcolor=vertex_colors, show_lines=False,name= f"SDF Mesh {target_layer}")
#                 print(f"Added field mesh for layer {target_layer}")
                
#                 # Add iso contour if available
#                 viewer.scene.add(contours.to_compas_network(), linecolor=Color.black(), linewidth=6,name= f"Mesh_Contour_{target_layer}")                        
#         except Exception as e:
#             print(f"Error adding field for layer {target_layer}: {e}")

# # Add SDF bounding box as a rectangle for the target layer
# if target_layer < len(slicer.min_SDF_bb) and target_layer < len(slicer.max_SDF_bb):
#     min_bb = slicer.min_SDF_bb[target_layer]
#     max_bb = slicer.max_SDF_bb[target_layer]
    
#     # Create rectangle vertices at z=0 (since we're visualizing in the XY plane)
#     z_coord = 0.0
#     rect_vertices = [
#         [min_bb[0], min_bb[1], z_coord],  # Bottom-left
#         [max_bb[0], min_bb[1], z_coord],  # Bottom-right
#         [max_bb[0], max_bb[1], z_coord],  # Top-right
#         [min_bb[0], max_bb[1], z_coord],  # Top-left
#     ]
    
#     # Create rectangle edges (closed loop)
#     rect_edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
    
#     # Create a network for the rectangle
#     sdf_rect_network = Network()
#     for i, vertex in enumerate(rect_vertices):
#         sdf_rect_network.add_node(i, x=vertex[0], y=vertex[1], z=vertex[2])
    
#     for edge in rect_edges:
#         sdf_rect_network.add_edge(edge[0], edge[1])
    
#     # Add the rectangle to the viewer
#     # viewer.scene.add(sdf_rect_network, linecolor=Color.red(), linewidth=10, name=f"SDF BB Rectangle {target_layer}",show_points=True, pointsize=12, pointcolor=Color.red())
#     # print(f"Added SDF bounding box rectangle for layer {target_layer}")
#     # print(f"  Min BB: [{min_bb[0]:.3f}, {min_bb[1]:.3f}, {min_bb[2]:.3f}]")
#     # print(f"  Max BB: [{max_bb[0]:.3f}, {max_bb[1]:.3f}, {max_bb[2]:.3f}]")
# else:
#     print(f"Warning: No SDF bounding box data available for layer {target_layer}")

# #####################fenjiexianjieshu








viewer.show()


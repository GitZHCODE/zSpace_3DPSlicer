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
cableMeshes = None
startPlane = None
endPlane = None
start_bracing_graph = None
end_bracing_graph = None
slicer = zSlicer()
slicer.min_bb = [-0.2,-0.5, 0.0]
slicer.max_bb = [1.2, 0.5, 0.0]
slicer.init_field(200, 200) # Initialize field resolution
print_height = 0.6  # Number of layers desired
print_width = 0.015   # Width of the print path
is_original_position = True
# bracing_type = "Y"
load_mesh_path=r"\\zaha-hadid.com\Data\Projects\1453_CODE\1453___research\res_linwo\carbcomn\20251209\blockMesh.obj"
load_cable0_path=r"\\zaha-hadid.com\Data\Projects\1453_CODE\1453___research\res_linwo\carbcomn\20251209\cableMesh0.obj"
load_cable1_path=r"\\zaha-hadid.com\Data\Projects\1453_CODE\1453___research\res_linwo\carbcomn\20251209\cableMesh1.obj"
load_planes_path=r"\\zaha-hadid.com\Data\Projects\1453_CODE\1453___research\res_linwo\carbcomn\20251209\userInput.json"
output_path = "./data/blockMesh_4_carb_contours.json"



##############viewer config
# Remove the grid
viewer.config.renderer.show_grid = False
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

def read_start_end_bracings(filePath):
    """Load start and end bracing lines from a JSON file as zGraph objects.
    
    Parameters
    ----------
    filePath : str
        Path to the JSON file containing bracing data.
    
    Returns
    -------
    tuple
        A tuple containing (start_graph, end_graph) where each is a zGraph object
        representing the bracing lines, or (None, None) if not found
    """
    try:
        with open(filePath, 'r') as file:
            data = json.load(file)
        
        if "bracings" not in data:
            print("Warning: bracings not found in JSON data.")
            return None, None
        
        bracings = data["bracings"]
        
        # Collect all start lines
        start_vertices = []
        start_edges = []
        start_vertex_index = 0
        
        for key in sorted(bracings.keys()):
            if key.startswith("startLine"):
                line_data = bracings[key]
                start_pt = line_data["start"]
                end_pt = line_data["end"]
                
                # Add vertices
                start_vertices.extend(start_pt)  # [x, y, z]
                start_vertices.extend(end_pt)    # [x, y, z]
                
                # Add edge connecting the two vertices
                start_edges.extend([start_vertex_index, start_vertex_index + 1])
                start_vertex_index += 2
        
        # Collect all end lines
        end_vertices = []
        end_edges = []
        end_vertex_index = 0
        
        for key in sorted(bracings.keys()):
            if key.startswith("endLine"):
                line_data = bracings[key]
                start_pt = line_data["start"]
                end_pt = line_data["end"]
                
                # Add vertices
                end_vertices.extend(start_pt)    # [x, y, z]
                end_vertices.extend(end_pt)      # [x, y, z]
                
                # Add edge connecting the two vertices
                end_edges.extend([end_vertex_index, end_vertex_index + 1])
                end_vertex_index += 2
        
        # Create zGraph objects
        start_graph = None
        end_graph = None
        
        if start_vertices:
            start_graph = zGraph()
            start_vertices_array = np.array(start_vertices, dtype=np.float64)
            start_edges_array = np.array(start_edges, dtype=np.int32)
            success = start_graph.create_graph(start_vertices_array, start_edges_array)
            if not success:
                print("Warning: Failed to create start bracing graph")
                start_graph = None
            else:
                print(f"Created start bracing graph with {len(start_vertices)//3} vertices and {len(start_edges)//2} edges")
        
        if end_vertices:
            end_graph = zGraph()
            end_vertices_array = np.array(end_vertices, dtype=np.float64)
            end_edges_array = np.array(end_edges, dtype=np.int32)
            success = end_graph.create_graph(end_vertices_array, end_edges_array)
            if not success:
                print("Warning: Failed to create end bracing graph")
                end_graph = None
            else:
                print(f"Created end bracing graph with {len(end_vertices)//3} vertices and {len(end_edges)//2} edges")
        
        return start_graph, end_graph
        
    except (KeyError, ValueError, FileNotFoundError) as e:
        print(f"Error parsing bracing data: {e}")
        return None, None

###sliders

def on_printHeight_slider_change(value):
    """Callback when slider value changes."""
    global print_height
    print_height = value / 1000.0  # Scale to 0.01 - 0.5
    slider_label.setText(f"Print Height: {print_height:.3f}")
    print(f"Slider value changed to: {print_height:.3f}")

# def on_bracing_slider_change(value):
#     global bracing_type
#     if value == 0:
#         bracing_type = "line"
#     elif value == 1:
#         bracing_type = "Y"
#     else:
#         bracing_type = "diagonal"
#     slider_bracing_label.setText(f"Bracing Type: {bracing_type}")
#     print(f"Bracing type changed to: {bracing_type}")

# Create a custom widget with slider
slider_widget = QWidget()
slider_layout = QVBoxLayout()

# Create label
slider_label = QLabel(f"Print Height: {print_height:.2f}")
slider_layout.addWidget(slider_label)
# Create label
# slider_bracing_label = QLabel(f"Bracing Type: {bracing_type}")
# slider_layout.addWidget(slider_bracing_label)
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
# slider_bracing = QSlider(Qt.Orientation.Horizontal)
# slider_bracing.setMinimum(0)
# slider_bracing.setMaximum(2)
# slider_bracing.setValue(0)  # Default value 1
# slider_bracing.setTickPosition(QSlider.TickPosition.TicksBelow)
# slider_bracing.setTickInterval(1)
# slider_bracing.valueChanged.connect(on_bracing_slider_change)

# slider_layout.addWidget(slider_bracing)

slider_widget.setLayout(slider_layout)



# Create a dock widget for the slider
dock = QDockWidget("Print Params", viewer.ui.window.widget)
dock.setWidget(slider_widget)
viewer.ui.window.widget.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, dock)

###################keypress event
############KEYTRIGGERED FUNCTION
def on_read_mesh():
    """Load mesh when key is pressed."""
    global mesh, startPlane, endPlane, start_bracing_graph, end_bracing_graph, is_original_position, cableMeshes
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
    cableMesh0 = read_mesh_from_obj(load_cable0_path)
    cableMesh1 = read_mesh_from_obj(load_cable1_path)
    cableMeshes = [cableMesh0, cableMesh1]
    startPlane, endPlane = read_start_end_planes(load_planes_path)
    start_bracing_graph, end_bracing_graph = read_start_end_bracings(load_planes_path)
    # Add mesh to viewer
    mObj = viewer.scene.add(mesh, linecolor=Color.grey(), linewidth=1, show_lines=True, opacity=1, name="Input",facecolor=Color.from_rgb255(200,200,200))
    cableObj0 = viewer.scene.add(cableMesh0, linecolor=Color.grey(), linewidth=1, show_lines=True, opacity=1, name="Cable0",facecolor=Color.from_rgb255(200,200,200))
    cableObj1 = viewer.scene.add(cableMesh1, linecolor=Color.grey(), linewidth=1, show_lines=True, opacity=1, name="Cable1",facecolor=Color.from_rgb255(200,200,200))
    mObj.init()
    viewer.renderer.buffer_manager.add_object(mObj)
    cableObj0.init()
    viewer.renderer.buffer_manager.add_object(cableObj0)
    cableObj1.init()
    viewer.renderer.buffer_manager.add_object(cableObj1)
    
    # Add start bracing graph to viewer if loaded successfully
    if start_bracing_graph is not None:
        try:
            start_network = start_bracing_graph.to_compas_network()
            if start_network.number_of_nodes() > 0:
                start_obj = viewer.scene.add(start_network, linecolor=Color.red(), linewidth=2, name="Start Bracing")
                start_obj.init()
                viewer.renderer.buffer_manager.add_object(start_obj)
                print(f"Added start bracing graph with {start_network.number_of_nodes()} vertices")
        except Exception as e:
            print(f"Error adding start bracing graph: {e}")
    
    # Add end bracing graph to viewer if loaded successfully
    if end_bracing_graph is not None:
        try:
            end_network = end_bracing_graph.to_compas_network()
            if end_network.number_of_nodes() > 0:
                end_obj = viewer.scene.add(end_network, linecolor=Color.blue(), linewidth=2, name="End Bracing")
                end_obj.init()
                viewer.renderer.buffer_manager.add_object(end_obj)
                print(f"Added end bracing graph with {end_network.number_of_nodes()} vertices")
        except Exception as e:
            print(f"Error adding end bracing graph: {e}")
    
    viewer.renderer.buffer_manager.create_buffers()
    viewer.renderer.update()
    viewer.ui.sidebar.update()
    print("mesh and bracing graphs added")

def on_computeFrames():
    """Perform slicing when key is pressed."""
    global mesh, startPlane, endPlane, slicer, contour_objects, start_bracing_graph, end_bracing_graph
    if mesh is None or startPlane is None or endPlane is None:
        print("Error: Mesh or planes not loaded. Please load mesh first.")
        return
    
    # Get the number of frames from slicer
    slicer.set_mesh(mesh)
    slicer.set_cable_meshes(cableMeshes)
    slicer.slice(startPlane, endPlane, print_height, start_plane_offset=0.01, end_plane_offset=0.01)
    
    # Set bracing graphs in slicer and compute interpolated versions
    if start_bracing_graph is not None and end_bracing_graph is not None:
        try:
            slicer.set_bracing_graphs(start_bracing_graph, end_bracing_graph)
            slicer.compute_interpolated_bracing_graphs()
            interpolated_bracing_graphs = slicer.get_interpolated_bracing_graphs()
            print(f"Computed {len(interpolated_bracing_graphs)} interpolated bracing graphs")
        except Exception as e:
            print(f"Error computing interpolated bracing graphs: {e}")
            interpolated_bracing_graphs = []
    else:
        interpolated_bracing_graphs = []
        print("Warning: Bracing graphs not available, skipping interpolation")
    
    # Get interpolated planes from slicer
    slicing_frames = slicer.get_frames()
    
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
    
    # Add interpolated bracing graphs to viewer
    for i, bracing_graph in enumerate(interpolated_bracing_graphs):
        if bracing_graph is not None:
            try:
                bracing_network = bracing_graph.to_compas_network()
                if bracing_network.number_of_nodes() > 0:
                    bracing_obj = viewer.scene.add(bracing_network, linecolor=Color.orange(), linewidth=1.5, name=f"Bracing {i}")
                    bracing_obj.init()
                    viewer.renderer.buffer_manager.add_object(bracing_obj)
                    print(f"Added interpolated bracing graph for layer {i}")
            except Exception as e:
                print(f"Error adding bracing graph for layer {i}: {e}")

    # Add cable graphs to viewer (one entry per cable per slice)
    try:
        for i, cable_layer in enumerate(slicer.cableGraphs):
            # cable_layer is expected to be a list of zGraph objects (one per cable mesh)
            if cable_layer is None:
                continue

            if isinstance(cable_layer, list):
                for j, cable_graph in enumerate(cable_layer):
                    if cable_graph is None:
                        continue
                    try:
                        cable_net = cable_graph.to_compas_network()
                        if cable_net.number_of_nodes() > 0:
                            cable_obj = viewer.scene.add(cable_net, linecolor=Color.black(), linewidth=1, name=f"CableGraph_{i}_{j}")
                            cable_obj.init()
                            viewer.renderer.buffer_manager.add_object(cable_obj)
                            print(f"Added cable graph for layer {i}, cable {j}")
                    except Exception as e:
                        print(f"Error adding cable graph for layer {i}, cable {j}: {e}")
            else:
                # Backwards compatibility: single graph per layer
                try:
                    cable_graph = cable_layer
                    if cable_graph is None:
                        continue
                    cable_net = cable_graph.to_compas_network()
                    if cable_net.number_of_nodes() > 0:
                        cable_obj = viewer.scene.add(cable_net, linecolor=Color.black(), linewidth=1, name=f"CableGraph {i}")
                        cable_obj.init()
                        viewer.renderer.buffer_manager.add_object(cable_obj)
                        print(f"Added cable graph for layer {i}")
                except Exception as e:
                    print(f"Error adding cable graph for layer {i}: {e}")
    except Exception:
        # If slicer.cableGraphs doesn't exist or is malformed, skip gracefully
        pass
    
    # ONLY call these ONCE after all objects are added
    viewer.renderer.buffer_manager.create_buffers()
    viewer.renderer.update()
    viewer.ui.sidebar.update()
    
    print(f"Slicing complete: {len(contour_objects)} contours and {len(interpolated_bracing_graphs)} bracing graphs added")

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
    
    slicer.update_all_contours(print_width)
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
                print("adding contour for layer:", i)
                network = contour.to_compas_network()
                print("network nodes:", network.number_of_nodes())
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



viewer.show()


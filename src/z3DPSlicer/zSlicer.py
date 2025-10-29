"""
zSlicer class for mesh slicing operations.
"""

from math import dist
from networkx import center, edges
import numpy as np
from compas.geometry import Point, Vector, Frame, Plane, Polyline
from compas.geometry import intersection_segment_plane
from compas.datastructures import Mesh as CompasMesh
from .zMesh import zMesh
from .zGraph import zGraph
from .zField import zField
from . import zUtils

class zSlicer:
    """A slicer class that uses zSpace mesh intersection for slicing operations."""
    
    def __init__(self):
        self.blockMesh = zMesh()
        self.sliceMesh = zMesh()
        self.frames = []
        self.contours = []  # Store as zGraph objects
        self.polygon_contours = []  # Store slice contours
        self.fields = []  # Store as list of zField objects for each layer
        self.bracings = []  # Store as list of zGraph objects for each layer
        self.trims = []  # Store as list of zGraph objects for each layer
        self.field_x_res = 50
        self.field_y_res = 50
        self.min_bb = [-2.0, -2.0, 0.0]
        self.max_bb = [2.0, 2.0, 0.0]
        self.min_SDF_bb = []  # SDF bounding box minimum for each layer
        self.max_SDF_bb = []  # SDF bounding box maximum for each layer
        self.first_transform = None  # Store the first layer transform for reference

    def set_mesh(self, compas_mesh):
        """Set the mesh to be sliced.
        
        Parameters
        ----------
        compas_mesh : compas.datastructures.Mesh
            The COMPAS mesh to slice
        """
        self.blockMesh.from_compas_mesh(compas_mesh)
        mesh_copy = compas_mesh.copy()
        mesh_copy.quads_to_triangles()
        self.sliceMesh.from_compas_mesh(mesh_copy)

    def init_field(self, x_res, y_res):
        # Initialize a single field template for now - will create individual fields per layer
        self.field_x_res = x_res
        self.field_y_res = y_res

    def compute_sdf_bounding_box(self, scalar, x_res, y_res, layer_index):
        """Compute the bounding box of an SDF scalar field based on zero threshold.
        
        Parameters
        ----------
        scalar : list or np.array
            The SDF scalar field values (negative = interior, positive = exterior)
        x_res : int
            Resolution in x direction
        y_res : int
            Resolution in y direction
        layer_index : int
            Index of the layer to store the bounding box for
        """
        values = scalar
        if values is None:
            return
        
        # Handle both list and numpy array cases
        try:
            if len(values) == 0:
                return
        except TypeError:
            return
        
        # Convert to numpy array
        values_array = np.array(values)
        
        # Create coordinate grids
        x_indices = np.arange(x_res)
        y_indices = np.arange(y_res)
        
        # Reshape values assuming C++ column-major layout (x varies first)
        values_2d = values_array.reshape((x_res, y_res)).T  # Transpose to match NumPy row-major
        xx, yy = np.meshgrid(x_indices, y_indices)
        
        # Flatten arrays
        xx_flat = xx.flatten()
        yy_flat = yy.flatten()
        values_flat = values_2d.flatten()
        
        # Focus on points near the zero level set (boundary)
        epsilon = 0.001  # Threshold for "near zero"
        boundary_mask = np.abs(values_flat) <= epsilon
        if not np.any(boundary_mask):
            # No boundary points, use all points
            x_coords = xx_flat
            y_coords = yy_flat
        else:
            x_coords = xx_flat[boundary_mask]
            y_coords = yy_flat[boundary_mask]
        
        if len(x_coords) == 0 or len(y_coords) == 0:
            return
            
        # Find min and max indices
        min_x_index = np.min(x_coords)
        max_x_index = np.max(x_coords)
        min_y_index = np.min(y_coords)
        max_y_index = np.max(y_coords)
        
        # Normalize to [0, 1] range
        min_x_normalized = min_x_index / (x_res - 1) if x_res > 1 else 0.0
        max_x_normalized = max_x_index / (x_res - 1) if x_res > 1 else 1.0
        min_y_normalized = min_y_index / (y_res - 1) if y_res > 1 else 0.0
        max_y_normalized = max_y_index / (y_res - 1) if y_res > 1 else 1.0
        
        # Convert to world coordinates
        bb_width = self.max_bb[0] - self.min_bb[0]
        bb_height = self.max_bb[1] - self.min_bb[1]
        
        min_world_x = self.min_bb[0] + min_x_normalized * bb_width
        max_world_x = self.min_bb[0] + max_x_normalized * bb_width
        min_world_y = self.min_bb[1] + min_y_normalized * bb_height
        max_world_y = self.min_bb[1] + max_y_normalized * bb_height
        min_world_z = self.min_bb[2]
        max_world_z = self.max_bb[2]
        
        # Ensure arrays are large enough for this layer
        while len(self.min_SDF_bb) <= layer_index:
            self.min_SDF_bb.append([0, 0, 0])
        while len(self.max_SDF_bb) <= layer_index:
            self.max_SDF_bb.append([0, 0, 0])
        
        # Store as arrays for this specific layer
        self.min_SDF_bb[layer_index] = [min_world_x, min_world_y, min_world_z]
        self.max_SDF_bb[layer_index] = [max_world_x, max_world_y, max_world_z]

    def compute_bracing_and_trim(self, layer_index, print_width, shape="line", line_number=3):
        """Compute bracing and trim for a specific layer.
        
        Parameters
        ----------
        layer_index : int
            Index of the layer
        print_width : float
            Width of the print path for trim computation
        shape : str
            Shape type for bracing (default: "line")
        line_number : int
            Number of lines to create for bracing (default: 3)
        """
        # Ensure the bracings and trims lists are large enough
        while len(self.bracings) <= layer_index:
            self.bracings.append(zGraph())
        while len(self.trims) <= layer_index:
            self.trims.append(zGraph())
            
        bracing_graph = zGraph()
        trim_graph = zGraph()
        
        # Line logic - create multiple horizontal lines distributed across the SDF bounding box
        if shape == "line":
            vertices = []
            edges = []
            
            # Make sure we have a bounding box for this layer
            if layer_index >= len(self.min_SDF_bb) or layer_index >= len(self.max_SDF_bb):
                print(f"Warning: SDF bounding box not computed for layer {layer_index}")
                return
            
            # Multiple lines distributed across SDF Y range
            y_min = self.min_SDF_bb[layer_index][1]
            y_max = self.max_SDF_bb[layer_index][1]
            
            # Distribute lines evenly across the Y range
            for i in range(line_number):
                if line_number > 1:
                    y_pos = y_min + (y_max - y_min) * i / (line_number - 1)
                else:
                    y_pos = (y_min + y_max) / 2  # Use middle if only one line
                
                # Add vertices for this line
                vertices.extend([
                    self.min_SDF_bb[layer_index][0], y_pos, 0.0,  # Start of line
                    self.max_SDF_bb[layer_index][0], y_pos, 0.0   # End of line
                ])
            
            # Create sequential edge connections [0,1,2,3,4,5] for line_number=3
            for i in range(0, line_number * 2 - 2, 2):
                edges.extend([i, i + 1])
            # edges = [0,1,2,3,4,5]
        
        elif shape == "Y":
            vertices = []
            edges = []
            
            # Make sure we have a bounding box for this layer
            if layer_index >= len(self.min_SDF_bb) or layer_index >= len(self.max_SDF_bb):
                print(f"Warning: SDF bounding box not computed for layer {layer_index}")
                return
            
            # Y shape logic - fixed positions for now
            vertices.extend([
                self.min_SDF_bb[layer_index][0], self.min_SDF_bb[layer_index][1], 0.0,  # Bottom left 0
                self.max_SDF_bb[layer_index][0], self.min_SDF_bb[layer_index][1], 0.0,   # Bottom right 1
                (self.min_SDF_bb[layer_index][0] + self.max_SDF_bb[layer_index][0]) / 2,(self.min_SDF_bb[layer_index][1] + self.max_SDF_bb[layer_index][1]) / 2,0.0,  # Center 2
                (self.min_SDF_bb[layer_index][0] + self.max_SDF_bb[layer_index][0]) / 2, self.max_SDF_bb[layer_index][1], 0.0,  # Top center 3
            ])

            edges.extend([0, 2, 1, 2, 3, 2])  # Connect bottom left to top center to bottom right

        elif shape == "diagonal":
            vertices = []
            edges = []
            
            # Make sure we have a bounding box for this layer
            if layer_index >= len(self.min_SDF_bb) or layer_index >= len(self.max_SDF_bb):
                print(f"Warning: SDF bounding box not computed for layer {layer_index}")
                return
            
            # Diagonal line from bottom-left to top-right
            vertices.extend([
                self.min_SDF_bb[layer_index][0], self.min_SDF_bb[layer_index][1], 0.0,  # Bottom left
                self.max_SDF_bb[layer_index][0], (self.max_SDF_bb[layer_index][1]+self.min_SDF_bb[layer_index][1]) / 2, 0.0,   # right middle
                self.min_SDF_bb[layer_index][0], self.max_SDF_bb[layer_index][1], 0.0   # Top left
            ])
            edges.extend([0, 1, 1, 2])
            
        # Create bracing graph
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)
        bracing_graph.create_graph(vertices_array, edges_array)
        self.bracings[layer_index] = bracing_graph
        
        # Create trim graph based on bracing edges
        trim_vertices = []
        trim_edges = []
        
        # Process bracing edges in pairs to create line segments
        for i in range(0, len(edges), 2):
            if i + 1 < len(edges):
                # Get the two vertex indices that form this edge
                v1_idx = edges[i]
                v2_idx = edges[i + 1]
                
                # Get vertex coordinates (each vertex has 3 coordinates)
                v1 = [vertices[v1_idx * 3], vertices[v1_idx * 3 + 1], vertices[v1_idx * 3 + 2]]
                v2 = [vertices[v2_idx * 3], vertices[v2_idx * 3 + 1], vertices[v2_idx * 3 + 2]]
                # Calculate point along the line segment (0.45 or 0.55 based on staggering)
                t = 0.7 if layer_index % 2 == 0 else 0.8
                point_on_line = [
                    v1[0] + t * (v2[0] - v1[0]),
                    v1[1] + t * (v2[1] - v1[1]),
                    v1[2] + t * (v2[2] - v1[2])
                ]
                
                # Calculate perpendicular direction (rotate 90 degrees in XY plane)
                line_dir = [v2[0] - v1[0], v2[1] - v1[1], 0]
                line_length = (line_dir[0]**2 + line_dir[1]**2)**0.5
                if line_length > 0:
                    # Normalize the line direction
                    line_dir = [line_dir[0]/line_length, line_dir[1]/line_length, 0]
                    # Get perpendicular direction (rotate 90 degrees)
                    perp_dir = [-line_dir[1], line_dir[0], 0]
                    
                    # Create trim line segment perpendicular to bracing edge
                    trim_start = [
                        point_on_line[0] + perp_dir[0] * 2 * print_width,
                        point_on_line[1] + perp_dir[1] * 2 * print_width,
                        0.0
                    ]
                    trim_end = [
                        point_on_line[0] - perp_dir[0] * 2 * print_width,
                        point_on_line[1] - perp_dir[1] * 2 * print_width,
                        0.0
                    ]
                    
                    # Add trim vertices
                    trim_start_idx = len(trim_vertices) // 3
                    trim_vertices.extend(trim_start)
                    trim_vertices.extend(trim_end)
                    
                    # Add trim edge
                    trim_edges.extend([trim_start_idx, trim_start_idx + 1])
        
        # Add additional trim edge using specified bracing vertices
        additional_v1 = [self.min_SDF_bb[0][0], self.min_SDF_bb[0][1], 0.0]  # Note: using min_SDF_bb[1] for Y coordinate
        additional_v2 = [self.max_SDF_bb[0][0], self.min_SDF_bb[0][1], 0.0]  # Note: using min_SDF_bb[1] for Y coordinate

        # Calculate point along the additional line segment (0.25 or 0.75 based on staggering)
        #trim for sdf outline
        t = 0.55 if layer_index % 2 == 0 else 0.6
        additional_point_on_line = [
            additional_v1[0] + t * (additional_v2[0] - additional_v1[0]),
            additional_v1[1] + t * (additional_v2[1] - additional_v1[1]),
            additional_v1[2] + t * (additional_v2[2] - additional_v1[2])
        ]
        
        # Calculate perpendicular direction for additional trim
        additional_line_dir = [additional_v2[0] - additional_v1[0], additional_v2[1] - additional_v1[1], 0]
        additional_line_length = (additional_line_dir[0]**2 + additional_line_dir[1]**2)**0.5
        if additional_line_length > 0:
            # Normalize the line direction
            additional_line_dir = [additional_line_dir[0]/additional_line_length, additional_line_dir[1]/additional_line_length, 0]
            # Get perpendicular direction (rotate 90 degrees)
            additional_perp_dir = [-additional_line_dir[1], additional_line_dir[0], 0]
            
            # Create additional trim line segment perpendicular to the additional bracing edge
            additional_trim_start = [
                additional_point_on_line[0] + additional_perp_dir[0] * 3 * print_width,
                additional_point_on_line[1] + additional_perp_dir[1] * 5 * print_width,
                0.0
            ]
            additional_trim_end = [
                additional_point_on_line[0] - additional_perp_dir[0] * 3 * print_width,
                additional_point_on_line[1] - additional_perp_dir[1] * 2 * print_width,
                0.0
            ]
            
            # Add additional trim vertices
            additional_trim_start_idx = len(trim_vertices) // 3
            trim_vertices.extend(additional_trim_start)
            trim_vertices.extend(additional_trim_end)
            
            # Add additional trim edge
            trim_edges.extend([additional_trim_start_idx, additional_trim_start_idx + 1])
        
        # Create trim graph
        if trim_vertices:
            trim_vertices_array = np.array(trim_vertices, dtype=np.float64)
            trim_edges_array = np.array(trim_edges, dtype=np.int32)
            trim_graph.create_graph(trim_vertices_array, trim_edges_array)
        
        self.trims[layer_index] = trim_graph

    def slice(self, start_plane, end_plane, print_height, start_plane_offset=0.01, end_plane_offset=0.01):
        """Slice the mesh using COMPAS edge-plane intersection and convert results to zGraph objects.
        
        This method uses COMPAS intersection_segment_plane to manually intersect mesh edges
        with cutting planes. The resulting intersection points are connected to form contours
        and converted to zGraph objects for further processing.
        
        Parameters
        ----------
        start_plane : compas.geometry.Frame or compas.geometry.Plane
            The starting plane for slicing
        end_plane : compas.geometry.Frame or compas.geometry.Plane  
            The ending plane for slicing
        print_height : float
            Height of each print layer in the same units as the mesh
        start_plane_offset : float, optional
            Distance to move the start plane inward (default: 0.01)
        end_plane_offset : float, optional
            Distance to move the end plane inward (default: 0.01)
        """
        if self.blockMesh is None:
            raise ValueError("No mesh set. Call set_mesh() first.")
        
        # Get plane origins and normals
        if hasattr(start_plane, 'point'):
            start_origin = start_plane.point
            start_normal = start_plane.zaxis if hasattr(start_plane, 'zaxis') else start_plane.normal
        else:
            start_origin = start_plane.point
            start_normal = start_plane.normal
            
        if hasattr(end_plane, 'point'):
            end_origin = end_plane.point
            end_normal = end_plane.zaxis if hasattr(end_plane, 'zaxis') else end_plane.normal
        else:
            end_origin = end_plane.point
            end_normal = end_plane.normal
        
        # Apply offsets to move planes inward
        # Move start plane forward by start_plane_offset
        adjusted_start_origin = start_origin + start_normal * start_plane_offset
        
        # Move end plane backward by end_plane_offset  
        adjusted_end_origin = end_origin - end_normal * end_plane_offset
        
        # Create adjusted planes
        if hasattr(start_plane, 'point'):
            # It's a Frame
            adjusted_start_plane = Frame(adjusted_start_origin, start_plane.xaxis, start_plane.yaxis)
            adjusted_end_plane = Frame(adjusted_end_origin, end_plane.xaxis, end_plane.yaxis)
        else:
            # It's a Plane
            adjusted_start_plane = Plane(adjusted_start_origin, start_normal)
            adjusted_end_plane = Plane(adjusted_end_origin, end_normal)
        
        # Calculate the distance between adjusted plane origins
        plane_distance = adjusted_start_origin.distance_to_point(adjusted_end_origin)
        
        if plane_distance == 0:
            raise ValueError("Start and end planes cannot be at the same location")
        
        # Calculate number of slices based on print height
        num_slices = int(plane_distance / print_height)
        if num_slices < 1:
            num_slices = 1
        
        print(f"COMPAS slicing with print_height={print_height}, plane_distance={plane_distance:.3f}, resulting in {num_slices} layers")
        print(f"Applied offsets: start_plane_offset={start_plane_offset}, end_plane_offset={end_plane_offset}")
            
        self.frames = []
        self.polygon_contours = []
        self.contours = []
        
        # Use the interpolate_plane function from zUtils with adjusted planes
        frames = zUtils.interpolate_plane(adjusted_start_plane, adjusted_end_plane, num_slices)
        
        # Use all interpolated frames - no exclusion needed since we've already adjusted the boundaries
        self.frames = frames
        
        # Convert mesh to COMPAS format for intersection
        compas_mesh = self.blockMesh.to_compas_mesh()
        mesh_vertices, mesh_faces = compas_mesh.to_vertices_and_faces()
        
        for frame in self.frames:
            origin = frame.point
            normal = frame.zaxis  # Use zaxis for the normal
            
            # Use manual edge-plane intersection method directly
            zgraph = self._manual_mesh_plane_intersection(compas_mesh, origin, normal)
            
            if zgraph is not None and zgraph.get_vertex_count() > 0:
                if zgraph is not None:

                    self.polygon_contours.append(zgraph)
                    self.contours.append(zgraph)
                else:
                    self.polygon_contours.append(None)
            else:
                self.polygon_contours.append(None)

    def _manual_mesh_plane_intersection(self, compas_mesh, plane_origin, plane_normal):
        """Manual mesh-plane intersection using COMPAS edge-plane intersections.
        
        Parameters
        ----------
        compas_mesh : compas.datastructures.Mesh
            The mesh to intersect
        plane_origin : compas.geometry.Point
            Origin point of the cutting plane
        plane_normal : compas.geometry.Vector
            Normal vector of the cutting plane
            
        Returns
        -------
        zGraph or None
            The resulting intersection graph, or None if no intersection
        """
        try:
            plane = (plane_origin, plane_normal)
            intersection_points = []
            intersection_edges = []
            
            # Get all mesh edges and check for plane intersections
            for edge in compas_mesh.edges():
                u, v = edge
                
                # Get vertex positions
                u_pos = compas_mesh.vertex_coordinates(u)
                v_pos = compas_mesh.vertex_coordinates(v)
                
                # Create edge segment
                edge_segment = (u_pos, v_pos)
                
                # Check intersection with plane
                intersection_point = intersection_segment_plane(edge_segment, plane)
                
                if intersection_point is not None:
                    intersection_points.append(intersection_point)
            
            if len(intersection_points) < 2:
                return None
            
            # Remove duplicate points
            unique_points = []
            tolerance = 0.0001
            
            for point in intersection_points:
                is_duplicate = False
                for existing_point in unique_points:
                    distance = ((point[0] - existing_point[0])**2 + 
                               (point[1] - existing_point[1])**2 + 
                               (point[2] - existing_point[2])**2) ** 0.5
                    if distance < tolerance:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_points.append(point)
            
            if len(unique_points) < 2:
                return None
            
            # Create vertices array
            all_vertices = []
            for point in unique_points:
                all_vertices.extend([float(point[0]), float(point[1]), float(point[2])])
            
            # Create edges connecting consecutive points (simple line segments)
            all_edges = []
            for i in range(len(unique_points) - 1):
                all_edges.extend([i, i + 1])

            all_edges.extend([len(unique_points) - 1, 0])  # Close the loop
            
            if len(all_vertices) == 0 or len(all_edges) == 0:
                return None
                
            # Create zGraph
            vertices_array = np.array(all_vertices, dtype=np.float64)
            edges_array = np.array(all_edges, dtype=np.int32)
            # print(f"Manual intersection produced {len(unique_points)} unique points.")
            # print("Unique Points:", unique_points)
            # print("Edges:", all_edges)
            zgraph = zGraph()
            success = zgraph.create_graph(vertices_array, edges_array)
            
            if success:
                return zgraph
            else:
                return None
                
        except Exception as e:
            print(f"Error in manual mesh-plane intersection: {e}")
            return None
    
    def update_contour(self, index, print_width,shape="line", line_number=3):
        """Update a specific contour by transforming it to frame coordinates, offsetting, and transforming back.
        
        Parameters
        ----------
        index : int
            Index of the contour to update
        print_width : float
            Width of the print path
        """
        if not self.frames or not self.polygon_contours:
            return

        if index >= len(self.polygon_contours) or index >= len(self.frames):
            return

        contour = self.polygon_contours[index]
        if contour is None:
            return

        # Ensure we have enough storage for this layer
        while len(self.fields) <= index:
            self.fields.append(zField())
        while len(self.centers) <= index:
            self.centers.append([0, 0, 0])

        frame = self.frames[index]
        
        # Get the transformation matrix for this frame using CORRECT transformations
        # Use the corrected functions that handle matrices properly
        tMatrix = zUtils.plane_to_plane(frame, Frame.worldXY())
        tMatrix_back = zUtils.plane_to_plane(Frame.worldXY(), frame)
        tMatrix_to_first = zUtils.plane_to_plane( frame,self.frames[0])
        if index == 0:
            self.first_transform = tMatrix # get the first layer transform for reference

        # Transform the zGraph to world coordinates
        contour.transform(tMatrix)
        self.polygon_contours[index] = contour

        # Create field for this layer
        field = self.fields[index]
        field.create_field(self.min_bb, self.max_bb, self.field_x_res, self.field_y_res)

        # Update contour based on distance field
        print(f"Updating contour {index} with print width {print_width}")
        scalars = field.get_scalars_polygon(contour, False)
        print(f"Scalars :{scalars}")
        print(f"Scalars range: [{np.min(scalars):.3f}, {np.max(scalars):.3f}]")
        if len(scalars) == 0:     
            print(f"Warning: scalars is empty for layer {index}, skipping update")
            return


        # Compute SDF bounding box for this layer
        self.compute_sdf_bounding_box(scalars, self.field_x_res, self.field_y_res, index)
        
        # Compute bracing and trim together
        self.compute_bracing_and_trim(index, print_width, shape, line_number)

        scalars_offseted_0 = scalars + 0.5 * print_width
        scalars_offseted_1 = scalars + 1.5 * print_width

        # Check if bracing and trim graphs have vertices before using them

        scalars_bracing = field.get_scalars_graph_edge_distance(self.bracings[index], print_width * 0.5, False)
        print(f"Scalars bracing range: [{np.min(scalars_bracing):.3f}, {np.max(scalars_bracing):.3f}]")
        scalars_bracing_trimmed_0 = field.boolean_subtract(scalars_offseted_1, scalars_bracing,  False)
        print(f"Scalars bracing trimmed 0 range: [{np.min(scalars_bracing_trimmed_0):.3f}, {np.max(scalars_bracing_trimmed_0):.3f}]")
        scalars_bracing_trimmed_1 = field.boolean_subtract(scalars_offseted_0, scalars_bracing_trimmed_0, False)
        print(f"Scalars bracing trimmed 1 range: [{np.min(scalars_bracing_trimmed_1):.3f}, {np.max(scalars_bracing_trimmed_1):.3f}]")


        scalars_trim = field.get_scalars_graph_edge_distance(self.trims[index], print_width * 0.5, False) #*0.9 to make sure tips touches
        print(f"Scalars trim range: [{np.min(scalars_trim):.3f}, {np.max(scalars_trim):.3f}]")

        result_scalars = field.boolean_subtract(scalars_bracing_trimmed_1, scalars_trim, False)

        # Debug: Check if result_scalars is valid
        if result_scalars is None:
            print(f"Warning: result_scalars is None for layer {index}")
            # Use the original scalars as fallback
            result_scalars = scalars
        

        field.set_field_values(result_scalars)
        field.smooth_field(num_smooth=1)
        contour = field.get_iso_contour(0.0)
        # contour = field.get_iso_contour_direct(0.0)
        # contour.merge_vertices(0.005)
        self.contours[index] = contour
        self.contours[index].transform(tMatrix_back)
        # self.contours[index].transform(self.first_transform)  # apply first layer transform to all layers for consistency
        # self.contours[index].transform(tMatrix_to_first)  # apply first layer transform to all layers for consistency
        # field.get_iso_contour(0)
        self.fields[index] = field


    def update_all_contours(self, print_width,shape="line", line_number=3):
        """Update all contours at once and store all geometries.
        
        Parameters
        ----------
        print_width : float
            Width of the print path (formerly called 'dist')
        """
        print(f"Updating all {len(self.polygon_contours)} contours with print width {print_width}")
        
        # Initialize storage lists to ensure they're the right size
        self.fields = []
        self.bracings = []
        self.trims = []
        self.centers = []

        for i in range(len(self.polygon_contours)):
            if self.polygon_contours[i] is not None:
                self.update_contour(i, print_width, shape, line_number)
                print(f"Updated contour {i}")
            else:
                # Add empty placeholders for None contours
                self.fields.append(zField())
                self.bracings.append(zGraph())
                self.trims.append(zGraph())
                self.centers.append([0, 0, 0])
                print(f"Skipped None contour {i}")
        
        print(f"All contours updated. Total fields: {len(self.fields)}")
    
    def get_frames(self):
        """Get the generated slicing frames.
        
        Returns
        -------
        list
            List of compas.geometry.Frame objects
        """
        return self.frames
    
    def get_contours(self):
        """Get the generated contour networks.
        
        Returns
        -------
        list
            List of compas.datastructures.Network objects (or None for empty intersections)
        """
        networks = []
        for contour in self.contours:
            if contour is not None:
                network = contour.to_compas_network()
                if network.number_of_nodes() > 0:
                    networks.append(network)
                else:
                    networks.append(None)
            else:
                networks.append(None)
        return networks
    
    def get_field(self, index=0):
        """Get the field for a specific layer.
        
        Parameters
        ----------
        index : int
            Index of the layer (default is 0)
            
        Returns
        -------
        zField or None
            The field for the specified layer, or None if not available
        """
        if index < len(self.fields):
            return self.fields[index]
        return None
        
    def get_fields(self):
        """Get all fields.
        
        Returns
        -------
        list
            List of zField objects for all layers
        """
        return self.fields

    def export_contours(self, filepath, print_width, print_height):
        """Export contours to a JSON file with print plane data.
        
        Parameters
        ----------
        filepath : str
            Path to save the JSON file
        print_width : float
            Width of the print path
        print_height : float
            Default print height (used for fallback cases)
        """
        import json
        import math
        
        contours_data = []
        # 1. change seam
        for i, contour in enumerate(self.contours):
            if contour is not None and i < len(self.frames):
                # Get current frame and center
                current_frame = self.frames[i]
                current_center = self.centers[i] if i < len(self.centers) else [0, 0, 0]
                
                # Convert zGraph to network for export
                network = contour.to_compas_network()
                
                # Get all vertices with their positions
                ordered_vertices = []
                for node in network.nodes():
                    xyz = network.node_attributes(node, 'xyz')
                    if xyz:
                        ordered_vertices.append([xyz[0], xyz[1], xyz[2]])
                
                # Create print plane data for each vertex
                print_planes = []
                for vertex_pos in ordered_vertices:
                    print_plane = {
                        'origin': vertex_pos,
                        'normal': [current_frame.zaxis.x, current_frame.zaxis.y, current_frame.zaxis.z],
                        'x_axis': [current_frame.xaxis.x, current_frame.xaxis.y, current_frame.xaxis.z],
                        'y_axis': [current_frame.yaxis.x, current_frame.yaxis.y, current_frame.yaxis.z]
                    }
                    print_planes.append(print_plane)
                
                # Calculate print height for each vertex (distance from vertex to next frame's plane)
                print_heights = []
                
                # Calculate per-vertex heights
                for j, vertex_pos in enumerate(ordered_vertices):
                    if i + 1 < len(self.frames):
                        # Calculate distance from current vertex to next frame's plane
                        next_frame = self.frames[i + 1]
                        current_point = Point(vertex_pos[0], vertex_pos[1], vertex_pos[2])
                        next_plane = Plane(next_frame.point, next_frame.zaxis)
                        vertex_height = next_plane.distance_to_point(current_point)
                        print_heights.append(vertex_height)
                    else:
                        prev_frame = self.frames[i - 1]
                        fallback_height = prev_frame.point.distance_to_point(current_frame.point)
                        print_heights.append(fallback_height)
                
                # Get edges in the new ordering
                edges = []
                for edge in network.edges():
                    edges.append(list(edge))
                
                contour_data = {
                    'layer_index': i,
                    'vertices': ordered_vertices,
                    'print_planes': print_planes,
                    'print_width': print_width,
                    'print_heights': print_heights,  # Now each vertex has its own height
                    'sdf_center': current_center,
                    'frame_origin': [current_frame.point.x, current_frame.point.y, current_frame.point.z],
                    'frame_normal': [current_frame.zaxis.x, current_frame.zaxis.y, current_frame.zaxis.z],
                    'edges': edges
                }
                
                contours_data.append(contour_data)
        
        # Export data
        export_data = {
            'print_data': contours_data,
            'total_layers': len(contours_data),
            'metadata': {
                'print_width': print_width,
                'field_resolution': [self.field_x_res, self.field_y_res],
                'bounding_box': {
                    'min': self.min_bb,
                    'max': self.max_bb
                }
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2) 
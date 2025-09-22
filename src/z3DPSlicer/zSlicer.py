"""
zSlicer class for mesh slicing operations.
"""

from math import dist
from networkx import edges
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
        self.fields = []  # Store as list of zField objects for each layer
        self.bracings = []  # Store as list of zGraph objects for each layer
        self.trims = []  # Store as list of zGraph objects for each layer
        self.centers = []  # Store center points for each layer
        self.field_x_res = 50
        self.field_y_res = 50
        self.min_bb = [-2.0, -2.0, 0.0]
        self.max_bb = [2.0, 2.0, 0.0]
        self.center = [0, 0, 0]  # Keep for compatibility

    def set_mesh(self, compas_mesh):
        """Set the mesh to be sliced.
        
        Parameters
        ----------
        compas_mesh : compas.datastructures.Mesh
            The COMPAS mesh to slice
        """
        self.blockMesh.from_compas_mesh(compas_mesh)
        compas_mesh.quads_to_triangles()
        self.sliceMesh.from_compas_mesh(compas_mesh)

    def init_field(self, x_res, y_res):
        # Initialize a single field template for now - will create individual fields per layer
        self.field_x_res = x_res
        self.field_y_res = y_res

    def compute_sdf_center(self, scalar, x_res, y_res, method='interior_centroid'):
        """Compute the geometry center of an SDF scalar field using SDF-aware methods.
        
        Parameters
        ----------
        scalar : list or np.array
            The SDF scalar field values (negative = interior, positive = exterior)
        x_res : int
            Resolution in x direction
        y_res : int
            Resolution in y direction
        method : str
            Method to use for center computation:
            - 'interior_centroid': Center of mass of interior points (negative values)
            - 'zero_level_centroid': Center of mass of zero-level set approximation
            - 'medial_axis': Approximate medial axis center (most negative point)
            - 'distance_weighted': Distance-weighted centroid focusing on interior
            
        Returns
        -------
        list
            Center as [x, y, z] coordinates in world space
        """
        values = scalar
        if values is None:
            return None
        
        # Handle both list and numpy array cases
        try:
            if len(values) == 0:
                return None
        except TypeError:
            return None
        
        # Convert to numpy array
        values_array = np.array(values)
        
        # Create coordinate grids
        x_indices = np.arange(x_res)
        y_indices = np.arange(y_res)
        xx, yy = np.meshgrid(x_indices, y_indices)
        
        # Flatten arrays
        xx_flat = xx.flatten()
        yy_flat = yy.flatten()
        values_flat = values_array.flatten()
        
        if method == 'interior_centroid':
            # Use only interior points (negative values)
            interior_mask = values_flat < 0
            if not np.any(interior_mask):
                # No interior points, fall back to zero-level method
                return self.compute_sdf_center(scalar, x_res, y_res, 'zero_level_centroid')
            
            # Weight by absolute value (more negative = more interior)
            weights = np.abs(values_flat[interior_mask])
            x_coords = xx_flat[interior_mask]
            y_coords = yy_flat[interior_mask]
            
        elif method == 'zero_level_centroid':
            # Focus on points near the zero level set (boundary)
            epsilon = 0.1  # Threshold for "near zero"
            boundary_mask = np.abs(values_flat) <= epsilon
            if not np.any(boundary_mask):
                # No boundary points, use all points with equal weight
                weights = np.ones_like(values_flat)
                x_coords = xx_flat
                y_coords = yy_flat
            else:
                # Weight inversely by distance to zero (closer to boundary = higher weight)
                weights = 1.0 / (np.abs(values_flat[boundary_mask]) + 1e-6)
                x_coords = xx_flat[boundary_mask]
                y_coords = yy_flat[boundary_mask]
                
        elif method == 'medial_axis':
            # Find the most negative point (deepest interior)
            min_idx = np.argmin(values_flat)
            center_x_index = xx_flat[min_idx]
            center_y_index = yy_flat[min_idx]
            
            # Convert directly to normalized coordinates
            center_x_normalized = center_x_index / (x_res - 1) if x_res > 1 else 0.5
            center_y_normalized = center_y_index / (y_res - 1) if y_res > 1 else 0.5
            
            # Convert to world coordinates
            bb_width = self.max_bb[0] - self.min_bb[0]
            bb_height = self.max_bb[1] - self.min_bb[1]
            world_x = self.min_bb[0] + center_x_normalized * bb_width
            world_y = self.min_bb[1] + center_y_normalized * bb_height
            world_z = self.min_bb[2]
            
            self.center = [world_x, world_y, world_z]
            return
            
        elif method == 'distance_weighted':
            # Weight points by their negative distance (interior focus)
            # Convert SDF to weights: more negative = higher weight
            weights = np.maximum(0, -values_flat)  # Only negative values contribute
            if np.sum(weights) == 0:
                # No negative values, fall back to simple centroid
                weights = np.ones_like(values_flat)
            x_coords = xx_flat
            y_coords = yy_flat
            
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Compute weighted centroid
        total_weight = np.sum(weights)
        if total_weight == 0:
            return None
            
        center_x_index = np.sum(x_coords * weights) / total_weight
        center_y_index = np.sum(y_coords * weights) / total_weight
        
        # Normalize to [0, 1] range
        center_x_normalized = center_x_index / (x_res - 1) if x_res > 1 else 0.5
        center_y_normalized = center_y_index / (y_res - 1) if y_res > 1 else 0.5
        
        # Convert to world coordinates
        bb_width = self.max_bb[0] - self.min_bb[0]
        bb_height = self.max_bb[1] - self.min_bb[1]
        world_x = self.min_bb[0] + center_x_normalized * bb_width
        world_y = self.min_bb[1] + center_y_normalized * bb_height
        world_z = self.min_bb[2]
        
        #  xy looks filped
        self.center = [world_y, world_x, world_z]


    def compute_bracing(self, layer_index, center_point):
        """Compute bracing for a specific layer.
        
        Parameters
        ----------
        layer_index : int
            Index of the layer
        center_point : list
            Center point [x, y, z] for this layer
        """
        # Ensure the bracings list is large enough
        while len(self.bracings) <= layer_index:
            self.bracings.append(zGraph())
            
        bracing_graph = zGraph()
        vertices = [
            self.min_bb[0], center_point[1], 0.0,  # First vertex: [min_x, center_y, 0]
            self.max_bb[0], center_point[1], 0.0   # Second vertex: [max_x, center_y, 0]
        ]
        edges = [0, 1]  # Define edges by vertex indices
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)
        bracing_graph.create_graph(vertices_array, edges_array)
        self.bracings[layer_index] = bracing_graph

    def compute_trim(self, print_width, contour_index, center_point):
        """Compute trim for a specific layer.
        
        Parameters
        ----------
        print_width : float
            Width of the print path for trim computation
        contour_index : int
            Index of the contour
        center_point : list
            Center point [x, y, z] for this layer
        """
        # Ensure the trims list is large enough
        while len(self.trims) <= contour_index:
            self.trims.append(zGraph())
            
        trim_graph = zGraph()
        #stagger logic
        if(contour_index%2==0):
            vertices = [
                center_point[0]-print_width, self.min_bb[1], 0.0,  # First vertex: [center_x, min_y, 0]
                center_point[0]-print_width,  center_point[1]+print_width*2 , 0.0   # Second vertex: [center_x, max_y, 0]
            ]
        else:
            vertices = [
                center_point[0]+print_width,  self.min_bb[1], 0.0,  # First vertex: [center_x, min_y, 0]
                center_point[0]+print_width,  center_point[1]+print_width*2, 0.0   # Second vertex: [center_x, max_y, 0]
            ]
        edges = [0, 1]  # Define edges by vertex indices
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)
        trim_graph.create_graph(vertices_array, edges_array)
        self.trims[contour_index] = trim_graph

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

                    self.contours.append(zgraph)
                else:
                    self.contours.append(None)
            else:
                self.contours.append(None)
    
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
    
    def update_contour(self, index, print_width):
        """Update a specific contour by transforming it to frame coordinates, offsetting, and transforming back.
        
        Parameters
        ----------
        index : int
            Index of the contour to update
        print_width : float
            Width of the print path
        """
        if not self.frames or not self.contours:
            return
            
        if index >= len(self.contours) or index >= len(self.frames):
            return
            
        contour = self.contours[index]
        if contour is None:
            return

        # Ensure we have enough storage for this layer
        while len(self.fields) <= index:
            self.fields.append(zField())
        while len(self.centers) <= index:
            self.centers.append([0, 0, 0])

        frame = self.frames[index]
        
        # Get the transformation matrix for this frame
        tMatrix = zUtils.plane_to_plane(frame, Frame.worldXY())
        tMatrix_back = zUtils.plane_to_plane(Frame.worldXY(), frame)

        # Transform the zGraph to world coordinates
        contour.transform(tMatrix)

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

        # Compute SDF-aware center using different methods
        # Method 1: Interior centroid (recommended for most SDF cases)
        self.compute_sdf_center(scalars, self.field_x_res, self.field_y_res, 'interior_centroid')
        
        # Store the center for this layer
        self.centers[index] = self.center.copy()
        
        self.compute_bracing(index, self.centers[index])
        self.compute_trim(print_width, index, self.centers[index])

        scalars_offseted_0 = scalars + 0.5 * print_width
        scalars_offseted_1 = scalars + 1.5 * print_width

        # Check if bracing and trim graphs have vertices before using them

        scalars_bracing = field.get_scalars_graph_edge_distance(self.bracings[index], print_width * 0.5, False)

        scalars_bracing_trimmed_0 = field.boolean_subtract(scalars_offseted_1, scalars_bracing,  False)
        scalars_bracing_trimmed_1 = field.boolean_subtract(scalars_offseted_0, scalars_bracing_trimmed_0, False)


        scalars_trim = field.get_scalars_graph_edge_distance(self.trims[index], print_width * 0.5 * 0.8, False) #*0.9 to make sure tips touches


        result_scalars = field.boolean_subtract(scalars_bracing_trimmed_1, scalars_trim, False)

        # Debug: Check if result_scalars is valid
        if result_scalars is None:
            print(f"Warning: result_scalars is None for layer {index}")
            # Use the original scalars as fallback
            result_scalars = scalars
        
        try:
            result_scalars_array = np.array(result_scalars)
            if len(result_scalars_array) == 0:
                print(f"Warning: result_scalars is empty for layer {index}")
                # Use the original scalars as fallback
                result_scalars = scalars
                result_scalars_array = np.array(result_scalars)
            
            # Check for invalid values
            if np.any(np.isnan(result_scalars_array)) or np.any(np.isinf(result_scalars_array)):
                print(f"Warning: result_scalars contains NaN or Inf values for layer {index}")
                # Replace invalid values with 0
                result_scalars_array = np.nan_to_num(result_scalars_array, nan=0.0, posinf=0.0, neginf=0.0)
                result_scalars = result_scalars_array.tolist()
            
            if len(result_scalars_array) > 0:
                print(f"Layer {index}: result_scalars range: [{np.min(result_scalars_array):.3f}, {np.max(result_scalars_array):.3f}]")
            
        except Exception as e:
            print(f"Error processing result_scalars for layer {index}: {e}")
            # Use original scalars as fallback
            result_scalars = scalars

        field.set_field_values(result_scalars)
        field.smooth_field(num_smooth=1)
        contour = field.get_iso_contour_direct(0.0)
        contour.merge_vertices(0.005)
        self.contours[index] = contour
        self.contours[index].transform(tMatrix_back)
        field.get_iso_contour(0)
        self.fields[index] = field
        #transform back the center point
        from compas.geometry import Transformation
        center_pt = Point(self.centers[index][0], self.centers[index][1], self.centers[index][2])
        # Use COMPAS Transformation for Point transformation instead of raw matrix
        transformation_back = Transformation.from_frame_to_frame(Frame.worldXY(), frame)
        center_pt.transform(transformation_back)
        self.centers[index] = [center_pt.x, center_pt.y, center_pt.z]

    def update_all_contours(self, print_width):
        """Update all contours at once and store all geometries.
        
        Parameters
        ----------
        print_width : float
            Width of the print path (formerly called 'dist')
        """
        print(f"Updating all {len(self.contours)} contours with print width {print_width}")
        
        # Initialize storage lists to ensure they're the right size
        self.fields = []
        self.bracings = []
        self.trims = []
        self.centers = []
        
        for i in range(len(self.contours)):
            if self.contours[i] is not None:
                self.update_contour(i, print_width)
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
                vertices_with_distances = []
                for node in network.nodes():
                    xyz = network.node_attributes(node, 'xyz')
                    if xyz:
                        vertex_pos = [xyz[0], xyz[1], xyz[2]]
                        # Calculate distance to SDF center
                        dist_to_center = math.sqrt(
                            (xyz[0] - current_center[0])**2 + 
                            (xyz[1] - current_center[1])**2 + 
                            (xyz[2] - current_center[2])**2
                        )
                        vertices_with_distances.append((node, vertex_pos, dist_to_center))
                
                # Sort vertices by distance to center (closest first for seam point)
                vertices_with_distances.sort(key=lambda x: x[2])
                
                # Reorder vertices starting from the closest to center (seam point)
                if vertices_with_distances:
                    seam_node = vertices_with_distances[0][0]
                    
                    # Build ordered vertex list starting from seam point
                    ordered_vertices = []
                    visited = set()
                    current_node = seam_node
                    
                    # Try to build a connected path from the seam point
                    while current_node is not None and current_node not in visited:
                        visited.add(current_node)
                        xyz = network.node_attributes(current_node, 'xyz')
                        if xyz:
                            ordered_vertices.append([xyz[0], xyz[1], xyz[2]])
                        
                        # Find next connected node that hasn't been visited
                        next_node = None
                        for neighbor in network.neighbors(current_node):
                            if neighbor not in visited:
                                next_node = neighbor
                                break
                        current_node = next_node
                    
                    # If we didn't get all vertices, add the remaining ones
                    if len(ordered_vertices) < len(vertices_with_distances):
                        for node, vertex_pos, _ in vertices_with_distances:
                            if node not in visited:
                                ordered_vertices.append(vertex_pos)
                    # updates contour vertices to new ordering
                    if ordered_vertices:
                        # Flatten vertex positions for zGraph
                        new_contour = zGraph()
                        vertices_flat = []
                        for vertex_pos in ordered_vertices:
                            vertices_flat.extend([vertex_pos[0], vertex_pos[1], vertex_pos[2]])
                        
                        # Create edges connecting consecutive vertices in a loop
                        edges_flat = []
                        num_vertices = len(ordered_vertices)
                        for j in range(num_vertices):
                            next_idx = (j + 1) % num_vertices  # Loop back to 0 at the end
                            edges_flat.extend([j, next_idx])
                        
                        # Update the contour using zGraph methods
                        vertices_array = np.array(vertices_flat, dtype=np.float64)
                        edges_array = np.array(edges_flat, dtype=np.int32)
                        new_contour.create_graph(vertices_array, edges_array)
                        self.contours[i] = new_contour

                else:
                    ordered_vertices = []
                
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
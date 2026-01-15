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
        self.blockMesh = zMesh() #for viz
        self.sliceMesh = zMesh() #for slicing operations
        self.cableMeshes = []  # Store cable meshes if needed - for viz
        self.cableSliceMeshes = []  # Store cable slice meshes if needed -for slicing operations
        self.frames = []
        self.contours = []  # Store as zGraph objects
        self.polygon_contours = []  # Store slice contours
        self.cableGraphs = []  # Store cable graphs if needed ,, a list per layer
        self.fields = []  # Store as list of zField objects for each layer
        self.bracings = []  # Store as list of zGraph objects for each layer
        self.trims = []  # Store as list of zGraph objects for each layer
        self.field_x_res = 50
        self.field_y_res = 50
        self.min_bb = [-2.0, -2.0, 0.0]
        self.max_bb = [2.0, 2.0, 0.0]
        self.userBracings = []  # bracing lines as zGraph objects for each layer
        # self.min_SDF_bb = []  # SDF bounding box minimum for each layer
        # self.max_SDF_bb = []  # SDF bounding box maximum for each layer
        self.first_transform = None  # Store the first layer transform for reference
        self.interpolated_bracing_graphs = []  # Store interpolated bracing graphs for each layer
        self.start_bracing_graph = None  # Reference start bracing graph
        self.end_bracing_graph = None  # Reference end bracing graph

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

    def set_cable_meshes(self, compas_meshes):
        """Set the cable meshes to be sliced.
        
        Parameters
        ----------
        compas_meshes : list of compas.datastructures.Mesh
            The list of COMPAS cable meshes to slice
        """
        self.cableMeshes = []
        self.cableSliceMeshes = []
        for compas_mesh in compas_meshes:
            zmesh = zMesh()
            zmesh.from_compas_mesh(compas_mesh)
            mesh_copy = compas_mesh.copy()
            mesh_copy.quads_to_triangles()
            zmesh_slice = zMesh()
            zmesh_slice.from_compas_mesh(mesh_copy)
            self.cableMeshes.append(zmesh)
            self.cableSliceMeshes.append(zmesh_slice)

    def set_bracing_graphs(self, start_bracing, end_bracing):
        """Set the start and end bracing graphs for interpolation.
        
        Parameters
        ----------
        start_bracing : zGraph
            The bracing graph at the start plane
        end_bracing : zGraph
            The bracing graph at the end plane
        """
        self.start_bracing_graph = start_bracing
        self.end_bracing_graph = end_bracing
    
    def compute_interpolated_bracing_graphs(self):
        """Compute interpolated and projected bracing graphs for all slicing frames.
        
        This method interpolates between start and end bracing graphs using the same
        number of samples as the slicing frames, and projects each onto its corresponding
        slicing plane.
        
        Raises
        ------
        ValueError
            If frames are not computed yet or bracing graphs are not set
        """
        if not self.frames:
            raise ValueError("No slicing frames available. Call slice() first.")
        
        if self.start_bracing_graph is None or self.end_bracing_graph is None:
            raise ValueError("Bracing graphs not set. Call set_bracing_graphs() first.")
        
        num_slices = len(self.frames)
        self.interpolated_bracing_graphs = []
        
        for i, frame in enumerate(self.frames):
            # Calculate interpolation parameter
            t = i / (num_slices - 1) if num_slices > 1 else 0.0
            
            # Interpolate bracing graph between start and end
            interpolated_graph = self.start_bracing_graph.interpolate(self.end_bracing_graph, t)
            
            # Project the interpolated graph onto the current slicing plane
            projected_graph = interpolated_graph.project_to_plane(frame)
            
            self.interpolated_bracing_graphs.append(projected_graph)
    
    def get_interpolated_bracing_graphs(self):
        """Get the computed interpolated bracing graphs.
        
        Returns
        -------
        list
            List of zGraph objects representing interpolated and projected bracing graphs
        """
        return self.interpolated_bracing_graphs

    def init_field(self, x_res, y_res):
        # Initialize a single field template for now - will create individual fields per layer
        self.field_x_res = x_res
        self.field_y_res = y_res

    def compute_bracing_and_trim(self, layer_index, print_width):
        """Compute bracing and trim for a specific layer using interpolated bracing graphs.
        
        Uses the pre-computed interpolated bracing graphs and creates perpendicular
        trim segments at the midpoint of each bracing line.
        
        Parameters
        ----------
        layer_index : int
            Index of the layer
        print_width : float
            Width of the print path for trim computation
        shape : str
            Shape type for bracing (ignored - uses interpolated graphs)
        line_number : int
            Number of lines to create for bracing (ignored - uses interpolated graphs)
        """
        # Ensure the bracings and trims lists are large enough
        while len(self.bracings) <= layer_index:
            self.bracings.append(zGraph())
        while len(self.trims) <= layer_index:
            self.trims.append(zGraph())
        
        # Use the interpolated bracing graph for this layer
        if layer_index < len(self.interpolated_bracing_graphs):
            bracing_graph = self.interpolated_bracing_graphs[layer_index]
            if bracing_graph is not None:
                self.bracings[layer_index] = bracing_graph
            else:
                print(f"Warning: No interpolated bracing graph available for layer {layer_index}")
                return
        else:
            print(f"Warning: Layer index {layer_index} exceeds interpolated bracing graphs count")
            return
        
        # Create trim graph based on interpolated bracing edges
        trim_vertices = []
        trim_edges = []
        
        # Get bracing graph data
        try:
            bracing_vertices, bracing_edges = bracing_graph.get_graph_data()
        except Exception as e:
            print(f"Error getting bracing graph data for layer {layer_index}: {e}")
            return
        
        bracing_vertices_list = bracing_vertices.tolist() if hasattr(bracing_vertices, 'tolist') else bracing_vertices
        bracing_edges_list = bracing_edges.tolist() if hasattr(bracing_edges, 'tolist') else bracing_edges
        
        # DEBUG: Print bracing graph structure
        print(f"DEBUG compute_bracing_and_trim layer {layer_index}:")
        print(f"  bracing_vertices shape: {bracing_vertices.shape if hasattr(bracing_vertices, 'shape') else 'list'}, length: {len(bracing_vertices_list)}")
        print(f"  bracing_edges shape: {bracing_edges.shape if hasattr(bracing_edges, 'shape') else 'list'}, length: {len(bracing_edges_list)}")
        print(f"  bracing_vertices_list (first 12): {bracing_vertices_list[:12]}")
        print(f"  bracing_edges_list (all): {bracing_edges_list}")
        print(f"  Number of vertices: {len(bracing_vertices_list) // 3}")
        print(f"  Number of edges (pairs): {len(bracing_edges_list) // 2}")
        
        # Process each edge to create perpendicular trim segments at midpoint
        # Edges are stored as consecutive pairs: [v0, v1, v2, v3, ...] where (v0,v1), (v2,v3) are edges
        for i in range(0, len(bracing_edges_list) - 1, 2):
            # Get the two vertex indices that form this edge
            v1_idx = bracing_edges_list[i]
            v2_idx = bracing_edges_list[i + 1]
            
            # Get vertex coordinates
            # Handle both flat arrays [x0,y0,z0,x1,y1,z1...] and nested lists [[x,y,z], [x,y,z]...]
            if isinstance(bracing_vertices_list[0], (list, tuple)):
                # Nested list format: [[x,y,z], [x,y,z], ...]
                v1 = list(bracing_vertices_list[v1_idx])
                v2 = list(bracing_vertices_list[v2_idx])
            else:
                # Flat array format: [x0,y0,z0,x1,y1,z1,...]
                v1 = [bracing_vertices_list[v1_idx * 3], 
                      bracing_vertices_list[v1_idx * 3 + 1], 
                      bracing_vertices_list[v1_idx * 3 + 2]]
                v2 = [bracing_vertices_list[v2_idx * 3], 
                      bracing_vertices_list[v2_idx * 3 + 1], 
                      bracing_vertices_list[v2_idx * 3 + 2]]
            
            # Calculate point along the line segment
            # Even layers use 0.45 (closer to v1), odd layers use 0.5 (midpoint)
            # Use linear interpolation: point = v1 + t * (v2 - v1)
            proportion = 0.45 if layer_index % 2 == 0 else 0.5
            midpoint = [
                v1[0] + proportion * (v2[0] - v1[0]),
                v1[1] + proportion * (v2[1] - v1[1]),
                v1[2] + proportion * (v2[2] - v1[2])
            ]
            
            # Calculate direction vector along the line
            line_dir = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]]
            line_length = (line_dir[0]**2 + line_dir[1]**2 + line_dir[2]**2)**0.5
            
            if line_length > 0:
                # Normalize the line direction
                line_dir = [line_dir[0]/line_length, line_dir[1]/line_length, line_dir[2]/line_length]
                
                # Get perpendicular direction (rotate 90 degrees in XY plane)
                perp_dir = [-line_dir[1], line_dir[0], 0]
                perp_length = (perp_dir[0]**2 + perp_dir[1]**2 + perp_dir[2]**2)**0.5
                
                if perp_length > 0:
                    # Normalize the perpendicular direction
                    perp_dir = [perp_dir[0]/perp_length, perp_dir[1]/perp_length, perp_dir[2]/perp_length]
                    
                    # Create trim line segment perpendicular to bracing edge at midpoint
                    # Extend perpendicular distance based on print_width
                    trim_extent = print_width * 2.0
                    
                    trim_start = [
                        midpoint[0] + perp_dir[0] * trim_extent,
                        midpoint[1] + perp_dir[1] * trim_extent,
                        midpoint[2] + perp_dir[2] * trim_extent
                    ]
                    trim_end = [
                        midpoint[0] - perp_dir[0] * trim_extent,
                        midpoint[1] - perp_dir[1] * trim_extent,
                        midpoint[2] - perp_dir[2] * trim_extent
                    ]
                    
                    # Add trim vertices
                    trim_start_idx = len(trim_vertices) // 3
                    trim_vertices.extend(trim_start)
                    trim_vertices.extend(trim_end)
                    
                    # Add trim edge
                    trim_edges.extend([trim_start_idx, trim_start_idx + 1])
        
        # Create trim graph
        if trim_vertices:
            trim_vertices_array = np.array(trim_vertices, dtype=np.float64)
            trim_edges_array = np.array(trim_edges, dtype=np.int32)
            trim_graph = zGraph()
            trim_graph.create_graph(trim_vertices_array, trim_edges_array)
            self.trims[layer_index] = trim_graph
        else:
            # Create empty trim graph if no trims were generated
            self.trims[layer_index] = zGraph()

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
        # Reset cableGraphs storage for this slicing operation
        self.cableGraphs = []
        
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
            
            # Use manual edge-plane intersection method directly for the main block mesh
            # zgraph = self._manual_mesh_plane_intersection(compas_mesh, origin, normal)
            #test use native zSpace slicing
            # print("Computing zSpace mesh-plane intersection for slicing...")
            zgraph = self.sliceMesh.intersect_plane(origin, normal)

            if zgraph is not None and zgraph.get_vertex_count() > 0:
                self.polygon_contours.append(zgraph)
                self.contours.append(zgraph)
            else:
                self.polygon_contours.append(None)

            # Slice each cable mesh separately and join their graphs into one per-layer graph
            # self.cableMeshes stores zMesh instances (set by set_cable_meshes)
            cable_layer_graphs = []

            print("cable slice mesh number:", len(self.cableSliceMeshes))
            for cable_zMesh in self.cableSliceMeshes:
                cg = cable_zMesh.intersect_plane(origin, normal)
                if cg is None:
                    continue
                # Only keep non-empty graphs
                try:
                    if cg.get_vertex_count() > 0:
                        cable_layer_graphs.append(cg)
                except Exception:
                    # If graph API differs, still try to append
                    cable_layer_graphs.append(cg)

            # Store all cable graphs for this layer as a list (one per cable mesh)
            if cable_layer_graphs:
                # keep list of zGraph objects for this layer
                self.cableGraphs.append(cable_layer_graphs)
            else:
                # Append empty list to preserve indexing per layer
                self.cableGraphs.append([])

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
        # Compute bracing and trim together
        self.compute_bracing_and_trim(index, print_width)

        # Get the transformation matrix for this frame using CORRECT transformations
        # Use the corrected functions that handle matrices properly
        tMatrix = zUtils.plane_to_plane(frame, Frame.worldXY())
        tMatrix_back = zUtils.plane_to_plane(Frame.worldXY(), frame)
        tMatrix_to_first = zUtils.plane_to_plane( frame,self.frames[0])
        if index == 0:
            self.first_transform = tMatrix # get the first layer transform for reference

        # Transform the zGraph to world coordinates
        contour.transform(tMatrix)
        for cable_graph in self.cableGraphs[index]:
            cable_graph.transform(tMatrix)
        self.bracings[index].transform(tMatrix)
        self.trims[index].transform(tMatrix)
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
        # self.compute_sdf_bounding_box(scalars, self.field_x_res, self.field_y_res, index)
        

        scalars_offseted_0 = scalars + 0.5 * print_width
        scalars_offseted_1 = scalars + 1.5 * print_width

        # Check if bracing and trim graphs have vertices before using them

        scalars_bracing = field.get_scalars_graph_edge_distance(self.bracings[index], print_width * 0.5, False)
        print(f"Scalars bracing range: [{np.min(scalars_bracing):.3f}, {np.max(scalars_bracing):.3f}]")
        scalars_bracing_trimmed_0 = field.boolean_subtract(scalars_offseted_1, scalars_bracing,  False)
        print(f"Scalars bracing trimmed 0 range: [{np.min(scalars_bracing_trimmed_0):.3f}, {np.max(scalars_bracing_trimmed_0):.3f}]")
        for i in range(len(self.cableGraphs[index])):
            scalars_cable = field.get_scalars_polygon(self.cableGraphs[index][i], False)
            scalars_total_cable = scalars_cable if i ==0 else field.boolean_union(scalars_cable, scalars_total_cable, False)
        scalars_bracing_trimmed_0_cable = field.boolean_subtract(scalars_bracing_trimmed_0, scalars_total_cable,  False)
        scalars_bracing_trimmed_1 = field.boolean_subtract(scalars_offseted_0, scalars_bracing_trimmed_0_cable, False)
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
        # contour = field.get_iso_contour(0.0)
        contour = field.get_iso_contour_direct(0.0)
        contour.merge_vertices(0.005)
        self.contours[index] = contour
        self.contours[index].transform(tMatrix_back)
        self.bracings[index].transform(tMatrix_back)
        self.trims[index].transform(tMatrix_back)
        for cable_graph in self.cableGraphs[index]:
            cable_graph.transform(tMatrix_back)
        print(f"Contour {index} updated with {self.contours[index].get_vertex_count()} vertices and {self.contours[index].get_edge_count()} edges")

        # self.contours[index].transform(self.first_transform)  # apply first layer transform to all layers for consistency
        # self.contours[index].transform(tMatrix_to_first)  # apply first layer transform to all layers for consistency
        # field.get_iso_contour(0)
        self.fields[index] = field

    def update_all_contours(self, print_width):
        """Update all contours at once and store all geometries.
        
        Parameters
        ----------
        print_width : float
            Width of the print path (formerly called 'dist')
        shape : str
            Shape type for bracing (ignored - uses interpolated graphs)
        line_number : int
            Number of lines to create for bracing (ignored - uses interpolated graphs)
        """
        print(f"Updating all {len(self.polygon_contours)} contours with print width {print_width}")
        
        # Compute interpolated bracing graphs if not already done
        if not self.interpolated_bracing_graphs and self.start_bracing_graph and self.end_bracing_graph:
            try:
                self.compute_interpolated_bracing_graphs()
                print(f"Computed {len(self.interpolated_bracing_graphs)} interpolated bracing graphs")
            except Exception as e:
                print(f"Error computing interpolated bracing graphs: {e}")
        
        # Initialize storage lists to ensure they're the right size
        self.fields = []
        self.bracings = []
        self.trims = []
        self.centers = []

        for i in range(len(self.polygon_contours)):
            if self.polygon_contours[i] is not None:
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
                current_center = [0, 0, 0]
                
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
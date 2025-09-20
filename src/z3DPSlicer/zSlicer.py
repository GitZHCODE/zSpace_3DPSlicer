"""
zSlicer class for mesh slicing operations.
"""

import numpy as np
from compas.geometry import Point, Vector, Frame
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
        self.field = zField() #resulf field
        self.bracings = zGraph()  # Store as zGraph objects
        self.trim =zGraph()
        self.field_x_res = 50
        self.field_y_res = 50
        self.min_bb = [-2.0, -2.0, 0.0]
        self.max_bb = [2.0, 2.0, 0.0]
        self.center = [0, 0, 0]

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
        # min_bb, max_bb, bboxMatrix= zUtils.get_bounding_box(self.sliceMesh.to_compas_mesh(), frame)

        # tMatrix = zUtils.plane_to_plane(frame, Frame.worldXY())

        # from compas.geometry import transform_points
        # min_bb = transform_points(min_bb, zUtils.get_transposed_tMatrix(tMatrix))
        # max_bb = transform_points(max_bb, zUtils.get_transposed_tMatrix(tMatrix))
        self.field.create_field(self.min_bb, self.max_bb, x_res, y_res)
        self.field_x_res = x_res
        self.field_y_res = y_res


    def network_as_bracing(self,network):
        zGraph_bracing = zGraph()
        zGraph_bracing.from_compas_network(network)
        self.bracings = zGraph_bracing


    def generate_bracing_lines(self,spacing = 0.5):
        print("Generating bracing lines...")
        
        # Define vertices for the line endpoints (flattened: x1,y1,z1, x2,y2,z2)
        vertices = [
            self.min_bb[0], -0.5, 0.0,  # First vertex: [0, min_y, 0]
                        # Second vertex: [0, 0, 0]
            self.max_bb[0], -0.5, 0.0   # Second vertex: [0, max_y, 0]
        ]   
        
        edges = [0, 1]  # Define edges by vertex indices
        
        # Convert to numpy arrays as required by create_graph
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)

        bracing_zGraph = zGraph()
        print(f"  Vertices array : {vertices_array}")
        print(f"  Edges array : {edges_array}")
        bracing_zGraph.create_graph(vertices_array, edges_array)

        if bracing_zGraph is not None and bracing_zGraph.get_vertex_count() > 0:
            # Store the zGraph directly
            self.bracings = bracing_zGraph
        else:
            raise Exception("Failed to create bracing zGraph")


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


    def compute_bracing(self):
        bracing_graph = zGraph()
        vertices = [
            self.min_bb[0], self.center[1], 0.0,  # First vertex: [min_x, center_y, 0]
            self.max_bb[0], self.center[1], 0.0   # Second vertex: [max_x, center_y, 0
        ]
        edges = [0, 1]  # Define edges by vertex indices
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)
        bracing_graph.create_graph(vertices_array, edges_array)
        self.bracings = bracing_graph

    def compute_trim(self, dist):
        trim_graph = zGraph()
        vertices = [
            self.center[0], self.min_bb[1], 0.0,  # First vertex: [center_x, min_y, 0]
            self.center[0],  self.center[1]+dist , 0.0   # Second vertex: [center_x, max_y, 0]
        ]
        edges = [0, 1]  # Define edges by vertex indices
        vertices_array = np.array(vertices, dtype=np.float64)
        edges_array = np.array(edges, dtype=np.int32)
        trim_graph.create_graph(vertices_array, edges_array)
        self.trim = trim_graph



    def slice(self, start_plane, end_plane, num_slices):
        """Slice the mesh between two planes.
        
        Parameters
        ----------
        start_plane : compas.geometry.Frame or compas.geometry.Plane
            The starting plane for slicing
        end_plane : compas.geometry.Frame or compas.geometry.Plane
            The ending plane for slicing
        num_slices : int
            Number of slices to generate between the planes
        """
        if self.sliceMesh is None:
            raise ValueError("No mesh set. Call set_mesh() first.")
            
        self.frames = []
        self.contours = []
        
        # Use the interpolate_plane function from zUtils
        frames = zUtils.interpolate_plane(start_plane, end_plane, num_slices)
        
        # Exclude the first and last plane
        if len(frames) > 2:
            frames = frames[1:-1]
        self.frames = frames
        
        for frame in frames:
            origin = frame.point
            normal = frame.zaxis  # Use zaxis for the normal

            # Perform intersection
            zgraph = self.sliceMesh.intersect_plane(
                [origin.x, origin.y, origin.z],
                [normal.x, normal.y, normal.z]
            )
            
            if zgraph is not None and zgraph.get_vertex_count() > 0:
                # Store the zGraph directly
                self.contours.append(zgraph)

            else:
                self.contours.append(None)
    
    def update_contour(self, index, dist):
        """Update a specific contour by transforming it to frame coordinates, offsetting, and transforming back.
        
        Parameters
        ----------
        index : int
            Index of the contour to update
        dist : float
            Offset value for the contours
        """
        if not self.frames or not self.contours:
            return
            
        if index >= len(self.contours) or index >= len(self.frames):
            return
            
        contour = self.contours[index]
        if contour is None:
            return

        frame = self.frames[index]
        
        # Get the transformation matrix for this frame
        tMatrix = zUtils.plane_to_plane(frame, Frame.worldXY())

        # Transform the zGraph to world coordinates
        contour.transform(tMatrix)
        contour.merge_vertices(0.001)



        # Update contour based on distance field
        print(f"Updating contour {index} with distance {dist}")
        scalars = self.field.get_scalars_polygon(contour, False)
        # self.field.set_field_values(scalars)
        # self.field.smooth_field(num_smooth=1)

        # Compute SDF-aware center using different methods
        # Try different methods and choose the best one for your use case:
        
        # Method 1: Interior centroid (recommended for most SDF cases)
        self.compute_sdf_center(scalars, self.field_x_res, self.field_y_res, 'interior_centroid')
        
        
        self.compute_bracing()
        # print(f"  Bracing vertex count: {self.bracings.get_vertex_count()}")
        self.compute_trim(dist)
        # print(f"  Trim vertex count: {self.trim.get_vertex_count()}")

        scalars_offseted = scalars + dist
        # print(f"scalars min: {np.min(scalars)}, max: {np.max(scalars)}")
        # print(f"scalars_offseted min: {np.min(scalars_offseted)}, max: {np.max(scalars_offseted)}")

        scalars_bracing = self.field.get_scalars_graph_edge_distance(self.bracings, dist * 0.5, False)
        # print(f"scalars_bracing min: {np.min(scalars_bracing)}, max: {np.max(scalars_bracing)}")
            # self.field.set_field_values(scalars_bracing)
        # self.field.smooth_field(num_smooth=1)




        scalars_bracing_trimmed_0 = self.field.boolean_subtract(scalars_offseted, scalars_bracing,  False)
        # print(f"scalars_bracing_trimmed_0 min: {np.min(scalars_bracing_trimmed_0)}, max: {np.max(scalars_bracing_trimmed_0)}")
        # self.field.set_field_values(scalars_bracing_trimmed_0)
        # self.field.smooth_field(num_smooth=1)
        scalars_bracing_trimmed_1 = self.field.boolean_subtract(scalars, scalars_bracing_trimmed_0, False)
        # print(f"scalars_bracing_trimmed_1 min: {np.min(scalars_bracing_trimmed_1)}, max: {np.max(scalars_bracing_trimmed_1)}")
        # self.field.set_field_values(scalars_bracing_trimmed_1)
        # self.field.smooth_field(num_smooth=1)   

        scalars_trim = self.field.get_scalars_graph_edge_distance(self.trim, dist * 0.5, False)

        # print(f"scalars_trim min: {np.min(scalars_trim)}, max: {np.max(scalars_trim)}")
        # self.field.set_field_values(scalars_trim)
        # self.field.smooth_field(num_smooth=1)

        result_scalars = self.field.boolean_subtract(scalars_bracing_trimmed_1, scalars_trim, False)


        self.field.set_field_values(result_scalars)
        self.field.smooth_field(num_smooth=1)

    def merge_contours(self,index, threshold=0.05):
            """Merge vertices in a specific contour based on a distance threshold.
            
            Parameters
            ----------
            index : int
                Index of the contour to merge
            threshold : float
                Distance threshold for merging vertices
            """
            if not self.contours:
                return
                
            if index >= len(self.contours):
                return
                
            contour = self.contours[index]
            if contour is None:
                return
                
            contour.merge_vertices(threshold)

    
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
    
    def get_field(self):
        return self.field
    
    def export_contours(self, filepath):
        """Export contours to a JSON file.
        
        Parameters
        ----------
        filepath : str
            Path to save the JSON file
        """
        import json
        
        contours_data = []
        for i, contour in enumerate(self.contours):
            if contour is not None:
                contour_data = {
                    'plane_index': i,
                    'vertices': [],
                    'edges': []
                }
                
                # Convert zGraph to network for export
                network = contour.to_compas_network()
                
                # Add vertices
                for node in network.nodes():
                    xyz = network.node_attributes(node, 'xyz')
                    if xyz:
                        contour_data['vertices'].append([xyz[0], xyz[1], xyz[2]])
                
                # Add edges
                for edge in network.edges():
                    contour_data['edges'].append(list(edge))
                
                contours_data.append(contour_data)
        
        with open(filepath, 'w') as f:
            json.dump(contours_data, f, indent=2) 
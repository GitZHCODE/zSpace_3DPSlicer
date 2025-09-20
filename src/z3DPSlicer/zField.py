from z3DPSlicer._zspace import Field as ZSpaceField, get_last_error
import numpy as np
from .zGraph import zGraph
from .zMesh import zMesh

# Diffusion type constants
Z_LAPLACIAN = 0
Z_AVERAGE = 1

class zField:
    def __init__(self):
        self.zfield = ZSpaceField()
        self._grid_res_x = None
        self._grid_res_y = None
        self._min_bb = None
        self._max_bb = None
        # self.field_value = None  # Store the latest field values

    def is_valid(self):
        return self.zfield.is_valid()

    def get_vertex_count(self):
        return self.zfield.get_vertex_count()

    def get_value_count(self):
        return self.zfield.get_value_count()

    def create_field(self, min_bb, max_bb, num_x, num_y):
        """Create a field with the given bounding box and resolution."""
        min_bb = np.array(min_bb, dtype=np.float64)
        max_bb = np.array(max_bb, dtype=np.float64)
        success = self.zfield.create_field(min_bb, max_bb, num_x, num_y)
        if not success:
            raise Exception(f"Failed to create field: {get_last_error()}")
        
        # Store grid resolution and bounding box for later use
        self._grid_res_x = num_x
        self._grid_res_y = num_y
        self._min_bb = min_bb.copy()
        self._max_bb = max_bb.copy()
        return self

    def get_grid_resolution(self):
        """Get the stored grid resolution (res_x, res_y) or None if not available."""
        if self._grid_res_x is not None and self._grid_res_y is not None:
            return (self._grid_res_x, self._grid_res_y)
        return None

    def get_stored_bounds(self):
        """Get the stored bounding box (min_bb, max_bb) or None if not available."""
        if self._min_bb is not None and self._max_bb is not None:
            return (self._min_bb.copy(), self._max_bb.copy())
        return None

    def set_grid_resolution(self, res_x, res_y):
        """Manually set the grid resolution if known."""
        self._grid_res_x = res_x
        self._grid_res_y = res_y

    def set_stored_bounds(self, min_bb, max_bb):
        """Manually set the stored bounding box if known."""
        self._min_bb = np.array(min_bb, dtype=np.float64)
        self._max_bb = np.array(max_bb, dtype=np.float64)

    def set_field_values(self, values):
        """Set field values."""
        values = np.array(values, dtype=np.float32)
        success = self.zfield.set_field_values(values)
        # self.field_value = values  # Store the latest field values
        if not success:
            raise Exception(f"Failed to set field values: {get_last_error()}")
        return self

    def get_field_values(self):
        """Get field values."""
        return self.zfield.get_field_values()

    def get_scalars_graph_edge_distance(self, graph, offset=0.0, normalise=True):
        """Calculate scalar field values based on distance to a graph's edges."""
        if not isinstance(graph, zGraph):
            raise ValueError("graph must be a zGraph instance")
        return self.zfield.get_scalars_graph_edge_distance(graph.zgraph, offset, normalise)

    def get_scalars_circle(self, centre, radius, offset=0.0, normalise=True):
        """Calculate scalar field values based on distance to a circle."""
        centre = np.array(centre, dtype=np.float64)
        return self.zfield.get_scalars_circle(centre, radius, offset, normalise)

    def get_scalars_line(self, start, end, offset=0.0, normalise=True):
        """Calculate scalar field values based on distance to a line."""
        start = np.array(start, dtype=np.float64)
        end = np.array(end, dtype=np.float64)
        return self.zfield.get_scalars_line(start, end, offset, normalise)

    def get_scalars_polygon(self, graph, normalise=True):
        """Calculate scalar field values based on distance to a polygon defined by a graph."""
        if not isinstance(graph, zGraph):
            raise ValueError("graph must be a zGraph instance")
        return self.zfield.get_scalars_polygon(graph.zgraph, normalise)

    def boolean_union(self, scalars_a, scalars_b, normalise=True):
        """Perform a boolean union operation between two scalar fields."""
        scalars_a = np.array(scalars_a, dtype=np.float32)
        scalars_b = np.array(scalars_b, dtype=np.float32)
        return self.zfield.boolean_union(scalars_a, scalars_b, normalise)

    def boolean_subtract(self, scalars_a, scalars_b, normalise=True):
        """Perform a boolean subtraction operation between two scalar fields."""
        scalars_a = np.array(scalars_a, dtype=np.float32)
        scalars_b = np.array(scalars_b, dtype=np.float32)
        return self.zfield.boolean_subtract(scalars_a, scalars_b, normalise)

    def boolean_intersect(self, scalars_a, scalars_b, normalise=True):
        """Perform a boolean intersection operation between two scalar fields."""
        scalars_a = np.array(scalars_a, dtype=np.float32)
        scalars_b = np.array(scalars_b, dtype=np.float32)
        return self.zfield.boolean_intersect(scalars_a, scalars_b, normalise)

    def boolean_difference(self, scalars_a, scalars_b, normalise=True):
        """Perform a boolean difference operation between two scalar fields."""
        scalars_a = np.array(scalars_a, dtype=np.float32)
        scalars_b = np.array(scalars_b, dtype=np.float32)
        return self.zfield.boolean_difference(scalars_a, scalars_b, normalise)

    def get_scalars_smin(self, scalars_a, scalars_b, k=1.0, mode=0):
        """Compute smooth minimum between two scalar fields."""
        scalars_a = np.array(scalars_a, dtype=np.float32)
        scalars_b = np.array(scalars_b, dtype=np.float32)
        return self.zfield.get_scalars_smin(scalars_a, scalars_b, k, mode)

    def get_scalars_smin_exponential_weighted(self, scalars_a, scalars_b, k=1.0, wt=0.5):
        """Compute weighted smooth minimum between two scalar fields using exponential mode."""
        scalars_a = np.array(scalars_a, dtype=np.float32)
        scalars_b = np.array(scalars_b, dtype=np.float32)
        return self.zfield.get_scalars_smin_exponential_weighted(scalars_a, scalars_b, k, wt)

    def get_scalars_smin_multiple(self, scalar_arrays, k=1.0, mode=0):
        """Compute smooth minimum across multiple scalar fields."""
        # Convert list of arrays to list of numpy arrays
        scalar_arrays = [np.array(arr, dtype=np.float32) for arr in scalar_arrays]
        return self.zfield.get_scalars_smin_multiple(scalar_arrays, k, mode)

    def get_bounds(self):
        """Get the field bounds."""
        return self.zfield.get_bounds()

    def get_iso_contour(self, threshold):
        """Get iso contour from the field at a given threshold value."""
        graph = zGraph(self.zfield.get_iso_contour(threshold))
        return graph

    def get_gradients(self):
        """Get field gradient vectors."""
        return self.zfield.get_gradients()

    def get_id(self, position):
        """Get the vertex ID at the given position."""
        position = np.array(position, dtype=np.float64)
        return self.zfield.get_id(position)

    def get_positions(self):
        """Get all vertex positions from the field."""
        return self.zfield.get_positions()

    def get_mesh(self):
        """Get the mesh representation of the field."""
        mesh = zMesh()
        mesh.zmesh = self.zfield.get_mesh()
        return mesh

    def get_iso_contour_direct(self, threshold, precision=6, dist_tolerance=1e-6):
        """
        Extract iso-contour lines directly from the field mesh using marching squares algorithm.
        
        Args:
            threshold: Threshold value for iso-contour extraction
            precision: Decimal precision for vertex position comparison (default: 6)
            dist_tolerance: Minimum distance tolerance for edge filtering (default: 1e-6)
            
        Returns:
            zGraph object containing the extracted iso-contour lines
        """
        # Get the mesh representation of the field
        mesh = self.get_mesh()
        if not mesh.is_valid():
            raise ValueError("Field mesh is not valid")
        
        # Get field values (scalars)
        scalars = self.get_field_values()
        if len(scalars) == 0:
            raise ValueError("No field values available")
        
        # Get mesh data
        vertices_array, poly_counts_array, poly_connections_array = mesh.get_mesh_data()
        vertices = vertices_array.tolist()
        poly_counts = poly_counts_array.tolist()
        poly_connections = poly_connections_array.tolist()
        
        if len(vertices) == 0 or len(poly_counts) == 0:
            # Return empty graph
            return zGraph()
        
        # Storage for contour vertices and edges
        positions = []
        edge_connects = []
        
        # Process each face
        connection_index = 0
        for face_idx, poly_count in enumerate(poly_counts):
            if poly_count not in [3, 4]:
                # Skip faces that are not triangles or quads
                connection_index += poly_count
                continue
            
            # Get face vertex indices
            face_vertices = []
            for i in range(poly_count):
                if connection_index < len(poly_connections):
                    vertex_idx = poly_connections[connection_index]
                    if 0 <= vertex_idx < len(vertices):
                        face_vertices.append(vertex_idx)
                    connection_index += 1
                else:
                    break
            
            if len(face_vertices) != poly_count:
                continue
            
            # Process triangle mesh
            if poly_count == 3:
                self._process_triangle_face(face_vertices, vertices, scalars, threshold, 
                                          positions, edge_connects, precision, dist_tolerance)
            
            # Process quad mesh
            elif poly_count == 4:
                self._process_quad_face(face_vertices, vertices, scalars, threshold, 
                                      positions, edge_connects, precision, dist_tolerance)
        
        # Create zGraph from extracted contour data
        if len(positions) == 0 or len(edge_connects) == 0:
            return zGraph()
        
        # Convert positions to numpy array
        positions_array = np.array(positions, dtype=np.float64).flatten()
        edge_connects_array = np.array(edge_connects, dtype=np.int32)
        
        # Create and return graph
        graph = zGraph()
        success = graph.create_graph(positions_array, edge_connects_array)
        if not success:
            raise Exception("Failed to create zSpace graph from iso-contour data")
        
        return graph
    
    def _process_triangle_face(self, face_vertices, vertices, scalars, threshold, 
                             positions, edge_connects, precision, dist_tolerance):
        """Process a triangular face for iso-contour extraction."""
        # Get vertex binary states (below threshold = True)
        vertex_binary = []
        for v_idx in face_vertices:
            vertex_binary.append(scalars[v_idx] < threshold)
        
        # Get marching squares case
        ms_case = self._get_isoline_case_triangle(vertex_binary)
        
        # Skip cases with no intersections
        if ms_case == 0 or ms_case == 7:
            return
        
        new_positions = []
        
        # Case 1 or 5: vertex 0 different from others
        if ms_case == 1 or ms_case == 6:
            v0_pos = np.array(vertices[face_vertices[0]])
            s0 = scalars[face_vertices[0]]
            
            v1_pos = np.array(vertices[face_vertices[1]])
            s1 = scalars[face_vertices[1]]
            pos1 = self._get_contour_position(threshold, v1_pos, v0_pos, s1, s0)
            
            v2_pos = np.array(vertices[face_vertices[2]])
            s2 = scalars[face_vertices[2]]
            pos2 = self._get_contour_position(threshold, v0_pos, v2_pos, s0, s2)
            
            new_positions.extend([pos1, pos2])
        
        # Case 2 or 5: vertex 1 different from others
        elif ms_case == 2 or ms_case == 5:
            v1_pos = np.array(vertices[face_vertices[1]])
            s1 = scalars[face_vertices[1]]
            
            v2_pos = np.array(vertices[face_vertices[2]])
            s2 = scalars[face_vertices[2]]
            pos1 = self._get_contour_position(threshold, v2_pos, v1_pos, s2, s1)
            
            v0_pos = np.array(vertices[face_vertices[0]])
            s0 = scalars[face_vertices[0]]
            pos2 = self._get_contour_position(threshold, v1_pos, v0_pos, s1, s0)
            
            new_positions.extend([pos1, pos2])
        
        # Case 3 or 4: vertex 2 different from others
        elif ms_case == 3 or ms_case == 4:
            v2_pos = np.array(vertices[face_vertices[2]])
            s2 = scalars[face_vertices[2]]
            
            v0_pos = np.array(vertices[face_vertices[0]])
            s0 = scalars[face_vertices[0]]
            pos1 = self._get_contour_position(threshold, v0_pos, v2_pos, s0, s2)
            
            v1_pos = np.array(vertices[face_vertices[1]])
            s1 = scalars[face_vertices[1]]
            pos2 = self._get_contour_position(threshold, v2_pos, v1_pos, s2, s1)
            
            new_positions.extend([pos1, pos2])
        
        # Add edge if positions are valid
        self._add_contour_edge(new_positions, positions, edge_connects, precision, dist_tolerance)
    
    def _process_quad_face(self, face_vertices, vertices, scalars, threshold, 
                         positions, edge_connects, precision, dist_tolerance):
        """Process a quad face for iso-contour extraction."""
        # Get vertex binary states (below threshold = True)
        vertex_binary = []
        for v_idx in face_vertices:
            vertex_binary.append(scalars[v_idx] < threshold)
        
        # Get marching squares case
        ms_case = self._get_isoline_case(vertex_binary)
        
        # Skip cases with no intersections
        if ms_case == 0 or ms_case == 15:
            return
        
        new_positions_1 = []
        new_positions_2 = []
        
        # Get vertex positions and scalars
        v_positions = [np.array(vertices[v_idx]) for v_idx in face_vertices]
        v_scalars = [scalars[v_idx] for v_idx in face_vertices]
        
        # Process each case according to marching squares lookup table
        if ms_case == 1:
            pos1 = self._get_contour_position(threshold, v_positions[1], v_positions[0], v_scalars[1], v_scalars[0])
            pos2 = self._get_contour_position(threshold, v_positions[0], v_positions[3], v_scalars[0], v_scalars[3])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 2:
            pos1 = self._get_contour_position(threshold, v_positions[0], v_positions[1], v_scalars[0], v_scalars[1])
            pos2 = self._get_contour_position(threshold, v_positions[2], v_positions[1], v_scalars[2], v_scalars[1])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 3:
            pos1 = self._get_contour_position(threshold, v_positions[3], v_positions[0], v_scalars[3], v_scalars[0])
            pos2 = self._get_contour_position(threshold, v_positions[2], v_positions[1], v_scalars[2], v_scalars[1])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 4:
            pos1 = self._get_contour_position(threshold, v_positions[1], v_positions[2], v_scalars[1], v_scalars[2])
            pos2 = self._get_contour_position(threshold, v_positions[3], v_positions[2], v_scalars[3], v_scalars[2])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 5:  # Saddle case - two separate contours
            # First contour
            pos1 = self._get_contour_position(threshold, v_positions[1], v_positions[0], v_scalars[1], v_scalars[0])
            pos2 = self._get_contour_position(threshold, v_positions[1], v_positions[2], v_scalars[1], v_scalars[2])
            new_positions_1.extend([pos1, pos2])
            
            # Second contour
            pos3 = self._get_contour_position(threshold, v_positions[3], v_positions[0], v_scalars[3], v_scalars[0])
            pos4 = self._get_contour_position(threshold, v_positions[3], v_positions[2], v_scalars[3], v_scalars[2])
            new_positions_2.extend([pos3, pos4])
            
        elif ms_case == 6:
            pos1 = self._get_contour_position(threshold, v_positions[0], v_positions[1], v_scalars[0], v_scalars[1])
            pos2 = self._get_contour_position(threshold, v_positions[3], v_positions[2], v_scalars[3], v_scalars[2])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 7:
            pos1 = self._get_contour_position(threshold, v_positions[3], v_positions[2], v_scalars[3], v_scalars[2])
            pos2 = self._get_contour_position(threshold, v_positions[3], v_positions[0], v_scalars[3], v_scalars[0])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 8:
            pos1 = self._get_contour_position(threshold, v_positions[0], v_positions[3], v_scalars[0], v_scalars[3])
            pos2 = self._get_contour_position(threshold, v_positions[2], v_positions[3], v_scalars[2], v_scalars[3])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 9:
            pos1 = self._get_contour_position(threshold, v_positions[1], v_positions[0], v_scalars[1], v_scalars[0])
            pos2 = self._get_contour_position(threshold, v_positions[2], v_positions[3], v_scalars[2], v_scalars[3])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 10:  # Saddle case - two separate contours
            # First contour
            pos1 = self._get_contour_position(threshold, v_positions[0], v_positions[1], v_scalars[0], v_scalars[1])
            pos2 = self._get_contour_position(threshold, v_positions[0], v_positions[3], v_scalars[0], v_scalars[3])
            new_positions_1.extend([pos1, pos2])
            
            # Second contour
            pos3 = self._get_contour_position(threshold, v_positions[2], v_positions[1], v_scalars[2], v_scalars[1])
            pos4 = self._get_contour_position(threshold, v_positions[2], v_positions[3], v_scalars[2], v_scalars[3])
            new_positions_2.extend([pos3, pos4])
            
        elif ms_case == 11:
            pos1 = self._get_contour_position(threshold, v_positions[2], v_positions[1], v_scalars[2], v_scalars[1])
            pos2 = self._get_contour_position(threshold, v_positions[2], v_positions[3], v_scalars[2], v_scalars[3])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 12:
            pos1 = self._get_contour_position(threshold, v_positions[0], v_positions[3], v_scalars[0], v_scalars[3])
            pos2 = self._get_contour_position(threshold, v_positions[1], v_positions[2], v_scalars[1], v_scalars[2])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 13:
            pos1 = self._get_contour_position(threshold, v_positions[1], v_positions[0], v_scalars[1], v_scalars[0])
            pos2 = self._get_contour_position(threshold, v_positions[1], v_positions[2], v_scalars[1], v_scalars[2])
            new_positions_1.extend([pos1, pos2])
            
        elif ms_case == 14:
            pos1 = self._get_contour_position(threshold, v_positions[0], v_positions[1], v_scalars[0], v_scalars[1])
            pos2 = self._get_contour_position(threshold, v_positions[0], v_positions[3], v_scalars[0], v_scalars[3])
            new_positions_1.extend([pos1, pos2])
        
        # Add edges for both contours
        self._add_contour_edge(new_positions_1, positions, edge_connects, precision, dist_tolerance)
        if len(new_positions_2) > 0:
            self._add_contour_edge(new_positions_2, positions, edge_connects, precision, dist_tolerance)
    
    def _add_contour_edge(self, new_positions, positions, edge_connects, precision, dist_tolerance):
        """Add a contour edge to the output arrays if it meets distance criteria."""
        if len(new_positions) != 2:
            return
        
        # Check edge length
        p0, p1 = new_positions[0], new_positions[1]
        edge_length = np.linalg.norm(p1 - p0)
        if edge_length < dist_tolerance:
            return
        
        # Add vertices and create edge
        edge_indices = []
        for pos in new_positions:
            exists, idx = self._check_repeat_vector(pos, positions, precision)
            if not exists:
                idx = len(positions)
                positions.append(pos)
            edge_indices.append(idx)
        
        edge_connects.extend(edge_indices)

    def smooth_field(self, scalars=None, num_smooth=1, diffuse_damp=0.1, diffusion_type=Z_LAPLACIAN, res_x=None, res_y=None):
        """
        Smooth the scalar field values using either Laplacian or Average diffusion.
        
        Args:
            scalars: Input scalar values array to smooth (optional, uses field values if None)
            num_smooth: Number of smoothing iterations (default: 1)
            diffuse_damp: Diffusion damping factor (default: 0.1)
            diffusion_type: Type of smoothing - Z_LAPLACIAN or Z_AVERAGE (default: Z_LAPLACIAN)
            res_x: Grid resolution in X direction (optional, will be estimated if not provided)
            res_y: Grid resolution in Y direction (optional, will be estimated if not provided)
        
        Returns:
            Smoothed scalar values array
        """
        # Use field values if no scalars provided
        if scalars is None:
            scalars = self.get_field_values()
        
        # Convert input to numpy array
        scalars = np.array(scalars, dtype=np.float32)
        
        # Check if we have a valid field
        if not self.is_valid():
            raise ValueError("Field is not valid")
        
        vertex_count = self.get_vertex_count()
        if len(scalars) != vertex_count:
            raise ValueError(f"Scalars array length ({len(scalars)}) must match vertex count ({vertex_count})")
        
        # Determine grid dimensions
        if res_x is not None and res_y is not None:
            # Use provided grid resolution
            grid_width = res_x
            grid_height = res_y
            
            if grid_width * grid_height != vertex_count:
                raise ValueError(f"Provided grid resolution ({res_x}x{res_y}={res_x*res_y}) doesn't match vertex count ({vertex_count})")
        else:
            # Use stored grid resolution if available
            stored_res = self.get_grid_resolution()
            if stored_res is not None:
                grid_width, grid_height = stored_res
                if grid_width * grid_height != vertex_count:
                    raise ValueError(f"Stored grid resolution ({grid_width}x{grid_height}={grid_width*grid_height}) doesn't match vertex count ({vertex_count})")
            else:
                # Fallback to simple implementation if no grid structure is available
                return self._smooth_field_simple(scalars, num_smooth, diffuse_damp, diffusion_type)
        
        # Reshape scalars to 2D grid for easier neighbor access
        scalars_2d = scalars.reshape((grid_height, grid_width))
        
        # Perform smoothing iterations
        for k in range(num_smooth):
            temp_values = np.zeros_like(scalars_2d)
            
            # Iterate through each grid cell
            for i in range(grid_height):
                for j in range(grid_width):
                    current_value = scalars_2d[i, j]
                    
                    # Get neighbor coordinates and values
                    neighbors = []
                    neighbor_coords = [
                        (i-1, j),   # top
                        (i+1, j),   # bottom
                        (i, j-1),   # left
                        (i, j+1),   # right
                        (i-1, j-1), # top-left
                        (i-1, j+1), # top-right
                        (i+1, j-1), # bottom-left
                        (i+1, j+1)  # bottom-right
                    ]
                    
                    # Collect valid neighbor values
                    for ni, nj in neighbor_coords:
                        if 0 <= ni < grid_height and 0 <= nj < grid_width:
                            neighbors.append(scalars_2d[ni, nj])
                    
                    # Apply smoothing based on diffusion type
                    if diffusion_type == Z_LAPLACIAN:
                        # Laplacian smoothing
                        lap_a = 0.0
                        
                        # Sum neighbor contributions
                        for neighbor_val in neighbors:
                            lap_a += neighbor_val * 1.0
                        
                        # Add center contribution (weighted by -8 as in original code)
                        lap_a += current_value * -8.0
                        
                        # Apply Laplacian operator with damping
                        new_value = current_value + (lap_a * diffuse_damp)
                        temp_values[i, j] = new_value
                        
                    elif diffusion_type == Z_AVERAGE:
                        # Average smoothing
                        if len(neighbors) > 0:
                            avg_value = np.mean(neighbors)
                            temp_values[i, j] = avg_value
                        else:
                            temp_values[i, j] = current_value
                    else:
                        # Unknown diffusion type, keep original value
                        temp_values[i, j] = current_value
            
            # Update scalars for next iteration
            scalars_2d = temp_values.copy()
            self.set_field_values(scalars_2d.flatten().astype(np.float32))
        
        # Flatten back to 1D array
        return scalars_2d.flatten().astype(np.float32)
    
    def smooth_field_inplace(self, num_smooth=1, diffuse_damp=0.1, diffusion_type=Z_LAPLACIAN, res_x=None, res_y=None):
        """
        Smooth the current field values in-place and update the field.
        
        Args:
            num_smooth: Number of smoothing iterations (default: 1)
            diffuse_damp: Diffusion damping factor (default: 0.1)
            diffusion_type: Type of smoothing - Z_LAPLACIAN or Z_AVERAGE (default: Z_LAPLACIAN)
            res_x: Grid resolution in X direction (optional, uses stored resolution)
            res_y: Grid resolution in Y direction (optional, uses stored resolution)
        
        Returns:
            Self for method chaining
        """
        # Get current field values and smooth them
        smoothed_values = self.smooth_field(None, num_smooth, diffuse_damp, diffusion_type, res_x, res_y)
        
        # Update the field with smoothed values
        self.set_field_values(smoothed_values)
        
        return self
    
    def _smooth_field_simple(self, scalars, num_smooth, diffuse_damp, diffusion_type):
        """
        Fallback smoothing method using spatial proximity for neighbor detection.
        Used when grid structure cannot be determined.
        """
        positions = self.get_positions()
        vertex_count = len(scalars)
        result_scalars = scalars.copy()
        
        # Get bounds for threshold calculation
        stored_bounds = self.get_stored_bounds()
        if stored_bounds is not None:
            min_bb, max_bb = stored_bounds
            bounds = (min_bb, max_bb)
        else:
            bounds = self.get_bounds()
        
        for k in range(num_smooth):
            temp_values = np.zeros_like(result_scalars)
            
            for i in range(vertex_count):
                current_pos = positions[i]
                current_value = result_scalars[i]
                
                # Find neighboring vertices using spatial proximity
                neighbors = []
                neighbor_values = []
                
                for j in range(vertex_count):
                    if i == j:
                        continue
                    
                    other_pos = positions[j]
                    dist = np.sqrt(np.sum((current_pos - other_pos)**2))
                    
                    # Use adaptive threshold based on field bounds
                    field_size = np.max(bounds[1] - bounds[0])
                    threshold = field_size / (vertex_count ** 0.5) * 1.5
                    
                    if dist < threshold:
                        neighbors.append(j)
                        neighbor_values.append(result_scalars[j])
                
                # Apply smoothing
                if diffusion_type == Z_LAPLACIAN:
                    lap_a = 0.0
                    for neighbor_val in neighbor_values:
                        lap_a += neighbor_val * 1.0
                    if len(neighbors) > 0:
                        lap_a += current_value * -len(neighbors)  # Adaptive center weight
                    new_value = current_value + (lap_a * diffuse_damp)
                    temp_values[i] = new_value
                elif diffusion_type == Z_AVERAGE:
                    if len(neighbor_values) > 0:
                        temp_values[i] = np.mean(neighbor_values)
                    else:
                        temp_values[i] = current_value
                else:
                    temp_values[i] = current_value
            
            result_scalars = temp_values.copy()
        
        return result_scalars
    
    def _get_isoline_case_triangle(self, vertex_binary):
        """
        Get marching squares case for triangular mesh based on vertex binary states.
        
        Args:
            vertex_binary: List of 3 boolean values indicating if vertices are below threshold
            
        Returns:
            Integer case ID (0-7) for marching squares lookup
        """
        case = 0
        if vertex_binary[0]:
            case += 1
        if vertex_binary[1]:
            case += 2
        if vertex_binary[2]:
            case += 4
        return case
    
    def _get_isoline_case(self, vertex_binary):
        """
        Get marching squares case for quad mesh based on vertex binary states.
        
        Args:
            vertex_binary: List of 4 boolean values indicating if vertices are below threshold
            
        Returns:
            Integer case ID (0-15) for marching squares lookup
        """
        case = 0
        if vertex_binary[0]:
            case += 1
        if vertex_binary[1]:
            case += 2
        if vertex_binary[2]:
            case += 4
        if vertex_binary[3]:
            case += 8
        return case
    
    def _get_contour_position(self, threshold, v1, v0, s1, s0):
        """
        Linear interpolation between two vertices based on scalar values and threshold.
        
        Args:
            threshold: Threshold value for iso-contour
            v1: First vertex position (numpy array)
            v0: Second vertex position (numpy array)
            s1: Scalar value at first vertex
            s0: Scalar value at second vertex
            
        Returns:
            Interpolated position as numpy array
        """
        if abs(s1 - s0) < 1e-10:  # Avoid division by zero
            return (v1 + v0) * 0.5
        
        t = (threshold - s0) / (s1 - s0)
        t = max(0.0, min(1.0, t))  # Clamp t to [0, 1]
        
        return v0 + t * (v1 - v0)
    
    def _check_repeat_vector(self, position, positions, precision=6):
        """
        Check if a position already exists in the positions list within tolerance.
        
        Args:
            position: Position to check (numpy array)
            positions: List of existing positions
            precision: Decimal precision for comparison
            
        Returns:
            Tuple (exists, index) - exists is bool, index is position in list if found
        """
        for i, existing_pos in enumerate(positions):
            diff = np.abs(position - existing_pos)
            if np.all(diff < 10**(-precision)):
                return True, i
        return False, -1 
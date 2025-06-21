from z3DPSlicer._zspace import Field as ZSpaceField, get_last_error
import numpy as np
from .zGraph import zGraph
from .zMesh import zMesh

class zField:
    def __init__(self):
        self.zfield = ZSpaceField()

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
        return self

    def set_field_values(self, values):
        """Set field values."""
        values = np.array(values, dtype=np.float32)
        success = self.zfield.set_field_values(values)
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
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
        self.field = zField()
        self.field_x_res = 50
        self.field_y_res = 50

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

    def init_field(self, frame, x_res, y_res):
        # min_bb, max_bb, bboxMatrix= zUtils.get_bounding_box(self.sliceMesh.to_compas_mesh(), frame)

        # tMatrix = zUtils.plane_to_plane(frame, Frame.worldXY())

        # from compas.geometry import transform_points
        # min_bb = transform_points(min_bb, zUtils.get_transposed_tMatrix(tMatrix))
        # max_bb = transform_points(max_bb, zUtils.get_transposed_tMatrix(tMatrix))
        min_bb = [-2, -2, 0]
        max_bb = [2, 2, 0]
        self.field.create_field(min_bb, max_bb, x_res, y_res)
        self.field_x_res = x_res
        self.field_y_res = y_res

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

        # Update contour based on distance field
        scalars = self.field.get_scalars_graph_edge_distance(contour, dist, True)
        self.field.set_field_values(scalars)
        contour = self.field.get_iso_contour(dist)
        
        # if contour is not None and contour.get_vertex_count() > 0:
        #     # Transform the new contour back to frame coordinates
        #     tMatrix_inverse = zUtils.get_inversed_tMatrix(tMatrix)
        #     contour.transform(tMatrix_inverse)
    
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
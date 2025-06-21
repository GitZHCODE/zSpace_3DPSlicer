"""
zSlicer class for mesh slicing operations.
"""

import numpy as np
from compas.geometry import Point, Vector, Frame
from compas.datastructures import Mesh as CompasMesh
from .zMesh import zMesh
from .zGraph import zGraph
from . import zUtils

class zSlicer:
    """A slicer class that uses zSpace mesh intersection for slicing operations."""
    
    def __init__(self):
        self.blockMesh = zMesh()
        self.sliceMesh = zMesh()
        self.frames = []
        self.contours = []
        
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
                # Convert to COMPAS network for visualization
                network = zgraph.to_compas_network()
                if network.number_of_nodes() > 0:
                    self.contours.append(network)
                else:
                    self.contours.append(None)
            else:
                self.contours.append(None)
    
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
        return [contour for contour in self.contours if contour is not None]
    
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
                
                # Add vertices
                for node in contour.nodes():
                    xyz = contour.node_attributes(node, 'xyz')
                    if xyz:
                        contour_data['vertices'].append([xyz[0], xyz[1], xyz[2]])
                
                # Add edges
                for edge in contour.edges():
                    contour_data['edges'].append(list(edge))
                
                contours_data.append(contour_data)
        
        with open(filepath, 'w') as f:
            json.dump(contours_data, f, indent=2) 
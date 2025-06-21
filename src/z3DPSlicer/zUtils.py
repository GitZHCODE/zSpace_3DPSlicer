# zspace utils

from z3DPSlicer._zspace import get_last_error

def get_zspace_error():
    return get_last_error() 

# compas utils
from compas.geometry import Point, Vector, Frame, Transformation

def interpolate_plane(start_plane, end_plane, steps):
    frames = []
    if hasattr(start_plane, 'point') and hasattr(start_plane, 'xaxis'):
        # It's a Frame, convert to Plane
        start_origin = start_plane.point
        start_normal = start_plane.zaxis
    else:
        # Assume it's already a Plane
        start_origin = start_plane.point
        start_normal = start_plane.normal
        
    if hasattr(end_plane, 'point') and hasattr(end_plane, 'xaxis'):
        # It's a Frame, convert to Plane
        end_origin = end_plane.point
        end_normal = end_plane.zaxis
    else:
        # Assume it's already a Plane
        end_origin = end_plane.point
        end_normal = end_plane.normal
    
    # Generate intermediate planes
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 0.5
        
        # Interpolate origin and normal
        origin = Point(
            start_origin.x + t * (end_origin.x - start_origin.x),
            start_origin.y + t * (end_origin.y - start_origin.y),
            start_origin.z + t * (end_origin.z - start_origin.z)
        )
        
        normal = Vector(
            start_normal.x + t * (end_normal.x - start_normal.x),
            start_normal.y + t * (end_normal.y - start_normal.y),
            start_normal.z + t * (end_normal.z - start_normal.z)
        )
        normal.unitize()
        
        # Create a frame with the interpolated origin and normal
        # We need to create proper x and y axes for the frame
        # Use the normal as z-axis and create perpendicular x and y axes
        z_axis = normal
        x_axis = Vector(1, 0, 0)  # Default x-axis
        if abs(z_axis.dot(x_axis)) > 0.9:  # If z is nearly parallel to x
            x_axis = Vector(0, 1, 0)  # Use y-axis instead
        y_axis = z_axis.cross(x_axis)
        y_axis.unitize()
        x_axis = y_axis.cross(z_axis)
        x_axis.unitize()
        
        frame = Frame(origin, x_axis, y_axis)
        frames.append(frame)
    
    return frames

def get_bounding_box(mesh, frame):
    """Get the bounding box of the mesh in the given frame.
    
    Parameters
    ----------
    mesh : compas.datastructures.Mesh
        The mesh to calculate bounding box for
    frame : compas.geometry.Frame
        The frame to transform the mesh coordinates to
        
    Returns
    -------
    tuple
        A tuple containing (min_point, max_point, transform_matrix) in the frame's coordinate system
    """
    from compas.geometry import Point, transform_points
    
    # Get all vertices from the mesh
    vertices = []
    for vertex in mesh.vertices():
        xyz = mesh.vertex_attributes(vertex, 'xyz')
        if xyz:
            vertices.append(Point(*xyz))
    
    if not vertices:
        return None, None, None
    
    # Transform vertices to the frame's coordinate system
    # First, transform to world coordinates if the frame is not at origin
    # Then transform to the frame's local coordinate system
    from compas.geometry import Transformation
    
    # Create transformation matrix from world to frame coordinates
    # The frame's x, y, z axes form the rotation matrix
    rotation_matrix = [
        [frame.xaxis.x, frame.yaxis.x, frame.zaxis.x, 0],
        [frame.xaxis.y, frame.yaxis.y, frame.zaxis.y, 0],
        [frame.xaxis.z, frame.yaxis.z, frame.zaxis.z, 0],
        [0, 0, 0, 1]
    ]
    
    # Create translation matrix to move origin to frame's point
    translation_matrix = [
        [1, 0, 0, -frame.point.x],
        [0, 1, 0, -frame.point.y],
        [0, 0, 1, -frame.point.z],
        [0, 0, 0, 1]
    ]
    
    # Combine transformations: first translate, then rotate
    from compas.geometry import multiply_matrices
    tMatrix = multiply_matrices(rotation_matrix, translation_matrix)
    
    # Transform all vertices
    transformed_vertices = transform_points(vertices, tMatrix)
    
    # Calculate bounding box
    if not transformed_vertices:
        return None, None, tMatrix
    
    x_coords = [v[0] for v in transformed_vertices]
    y_coords = [v[1] for v in transformed_vertices]
    z_coords = [v[2] for v in transformed_vertices]
    
    min_point = Point(min(x_coords), min(y_coords), min(z_coords))
    max_point = Point(max(x_coords), max(y_coords), max(z_coords))
    
    return min_point, max_point, tMatrix

def plane_to_plane(from_plane, to_plane):
    """Compute transformation matrix to transform from one plane to another.
    
    Parameters
    ----------
    from_plane : compas.geometry.Frame or compas.geometry.Plane
        The source plane/frame
    to_plane : compas.geometry.Frame or compas.geometry.Plane
        The target plane/frame
        
    Returns
    -------
    list
        4x4 transformation matrix
    """
    from compas.geometry import Transformation
    # Create transformation from world to from_frame
    from_transform = Transformation.from_frame(from_plane)
    
    # Create transformation from world to to_frame
    to_transform = Transformation.from_frame(to_plane)
    
    # The transformation from from_frame to to_frame is:
    # to_frame * from_frame^(-1)
    from compas.geometry import matrix_inverse, multiply_matrices
    
    # Get the transformation matrices
    from_matrix = from_transform.matrix
    to_matrix = to_transform.matrix
    
    # Compute inverse of from_frame transformation
    from_inverse = matrix_inverse(from_matrix)
    
    # Compute the final transformation: to_frame * from_frame^(-1)
    tMatrix = multiply_matrices(to_matrix, from_inverse)

    transformation = Transformation(tMatrix)
    transformation.transpose()

    return transformation.matrix

def get_inversed_tMatrix(tMatrix):
    """Get the inverse of a transformation matrix.
    
    Parameters
    ----------
    tMatrix : list or numpy.ndarray
        4x4 transformation matrix
        
    Returns
    -------
    list
        Inverse 4x4 transformation matrix
    """
    from compas.geometry import matrix_inverse
    return matrix_inverse(tMatrix)

def get_transposed_tMatrix(tMatrix):
    """Get the transpose of a transformation matrix.
    
    Parameters
    ----------
    tMatrix : list or numpy.ndarray
        4x4 transformation matrix
        
    Returns
    -------
    list
        Transposed 4x4 transformation matrix
    """
    import numpy as np
    if isinstance(tMatrix, list):
        tMatrix = np.array(tMatrix)
    return tMatrix.T.tolist()



# zspace utils

from z3DPSlicer._zspace import get_last_error

def get_zspace_error():
    return get_last_error() 

# compas utils
from compas.geometry import Point, Vector, Frame

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
import numpy as np
from z3DPSlicer import zSlicer, zMesh, zPlane

# # Create a simple cube mesh
# vertices = np.array([
#     [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
#     [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
# ], dtype=np.float32)

# faces = np.array([
#     [0, 1, 2], [0, 2, 3],  # bottom
#     [4, 6, 5], [4, 7, 6],  # top
#     [0, 4, 1], [1, 4, 5],  # front
#     [2, 6, 3], [3, 6, 7],  # back
#     [0, 3, 4], [3, 7, 4],  # left
#     [1, 5, 2], [2, 5, 6]   # right
# ], dtype=np.int32)

# # Create zMesh
# zmesh = zMesh()
# zmesh.setVertices(vertices)
# zmesh.setFaces(faces)

# # Create zPlane (horizontal plane at z=0.5)
# zplane = zPlane()
# zplane.setOrigin(np.array([0, 0, 0.5], dtype=np.float32))
# zplane.setNormal(np.array([0, 0, 1], dtype=np.float32))

# # Create zSlicer and slice
# slicer = zSlicer()
# slicer.setMesh(zmesh)
# contours = slicer.slice(zplane)

# print(f"Found {len(contours)} contours")
# for i, contour in enumerate(contours):
#     print(f"Contour {i}: {contour.shape[0]} points")
#     print(f"First few points: {contour[:3]}") 
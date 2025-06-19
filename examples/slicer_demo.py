# import slicer from compas_slicer
import compas
from compas.datastructures import Mesh
# from z3DPSlicer.datastructures import Slicer
from compas_viewer import Viewer

mesh = Mesh.from_json
# setup viewer

# import block
# myMesh = compass.Mesh.from_obj("path/to/your/mesh.obj")

# setup slicer
# slicer.set_mesh(myMesh)

# slice comput
# slicer.sclice(start, end, step)

## ... 
# slicer.add_brace
# slicer.postprocess
## ... 

# get contours from slicer
# contours = slicer.get_contours()

# exprot to json
# contours.export("path/to/contours.json")
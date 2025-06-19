# import slicer from compas_slicer
import compas
#from compas.datastructures import Mesh
#from z3DPSlicer import CompasMesh as Mesh
from z3DPSlicer.datastructures.zBlock import ZBlock
from compas_viewer import Viewer

local_path = "./data/blockMesh_23.json"
zblock = ZBlock()
zblock.from_zjson(local_path)
mesh = zblock.mesh
startPlane = zblock.startPlane
endPlane = zblock.endPlane
viewer = Viewer()
viewer.scene.add(mesh)
viewer.scene.add(startPlane)
viewer.scene.add(startPlane.point)
viewer.scene.add(endPlane)
viewer.scene.add(endPlane.point)
viewer.show()


# zblock.read_start_end_planes(local_path)

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
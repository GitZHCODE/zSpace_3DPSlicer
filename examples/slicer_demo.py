# import slicer from compas_slicer
import compas
#from compas.datastructures import Mesh
#from z3DPSlicer import CompasMesh as Mesh
from z3DPSlicer.datastructures.zBlock import ZBlock
from compas_viewer import Viewer

local_path = "C:/Users/Wo.Lin/source/repos/zspace_alice/EXE/data/IN/blockJson/blockMesh_0.json"
zblock = ZBlock()
zblock.from_zjson(local_path)
mesh = zblock.mesh
viewer = Viewer()
viewer.scene.add(mesh)
viewer.show()


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
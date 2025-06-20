from compas.geometry import Frame
from numpy import array

# convert a transformation matrix to a frame
def tMatrixToFrame(tMatrix):
    # create a frame from a transformation matrix
    frame = Frame(tMatrix[0:3], tMatrix[3:6], tMatrix[6:9])
    return frame
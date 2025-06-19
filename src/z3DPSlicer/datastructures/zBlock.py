####zBlock implementation using compas data with mesh and add on attributes set from zJson####
from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Point, Frame, Plane , Transformation
import json



class ZBlock(Data):
    def __init__(self):
        super().__init__()
        # note that if the code needs to be compatible with IronPython
        # you should write the following:
        # super(SomeThing, self).__init__()
        self.mesh = Mesh()
        self.startPlane = Plane()
        self.endPlane = Plane()

    
    def from_zjson(self, filePath):
            """Load mesh data from a JSON created by zSpace and return a ZBlock instance.
            
            Parameters
            ----------
            cls : type
                The class to instantiate (should be ZBlock).
            filePath : str
                Path to the JSON file created by zSpace.
            
            Returns
            -------
            ZBlock
                An instance of ZBlock with mesh data loaded from the JSON.
            """
            self.read_mesh_from_zJSON(filePath)



    def read_mesh_from_zJSON(self, filePath):
        """Load mesh data from a JSON created by zSpace and update self.mesh.
        
        Parameters
        ----------
        filePath : str
            Path to the JSON file created by zSpace.
        """

        # Load the JSON data
        with open(filePath, 'r') as file:
            data = json.load(file)
        
        print(f"Loaded JSON data from: {filePath}")
        
        # Extract vertex positions from VertexAttributes
        vertices = []
        if "VertexAttributes" in data:
            for attr_list in data["VertexAttributes"]:
                # Each vertex has x,y,z at the beginning (based on C++ code)
                # Different formats might have 3, 6, 9 or 15 values per vertex
                if len(attr_list) >= 3:
                    x, y, z = attr_list[0:3]
                    vertices.append([x, y, z])
        
        # If no vertices were found in VertexAttributes, try another approach
        if not vertices and "Vertices" in data:
            # This is a fallback, exact structure depends on how zSpace stores mesh data
            print("Using fallback vertex loading method")
            vertices = data["Vertices"]
            
        # Extract faces from the JSON
        faces = []
        if "Faces" in data and "Halfedges" in data:
            # Need to reconstruct faces from half-edge structure
            face_start_halfedges = data["Faces"]
            halfedges = data["Halfedges"]
            
            for face_he_idx in face_start_halfedges:
                if face_he_idx == -1:
                    continue
                    
                face_vertices = []
                current_he_idx = face_he_idx
                
                # Follow halfedges to build the face loop
                while True:
                    # Get vertex from halfedge
                    if current_he_idx >= 0 and current_he_idx < len(halfedges):
                        halfedge = halfedges[current_he_idx]
                        if len(halfedge) > 2:  # Ensure halfedge has vertex info
                            vertex_idx = halfedge[2]  # Based on C++ code, vertex index is at position 2
                            face_vertices.append(vertex_idx)
                        
                        # Move to next halfedge in the face
                        current_he_idx = halfedge[1]  # Next halfedge index
                        
                        # Break if we've looped back to start
                        if current_he_idx == face_he_idx:
                            break
                    else:
                        break
                
                if len(face_vertices) >= 3:
                    faces.append(face_vertices)
        
        # As a fallback, check if there's a more direct representation of faces
        if not faces and "FaceIndices" in data:
            faces = data["FaceIndices"]
        
        # Update self.mesh from vertices and faces
        if vertices and faces:
            print(f"Updating mesh with {len(vertices)} vertices and {len(faces)} faces")
            self.mesh = Mesh.from_vertices_and_faces(vertices, faces)
        else:
            print(f"Warning: Could not extract vertices and faces from JSON data")
            print(f"Vertices found: {len(vertices)}, Faces found: {len(faces)}")
            self.mesh = Mesh()
            
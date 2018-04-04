"""
Reads in a .bobj file from blender cache files (fluid simulation), in order to overwrite it with FDS results
"""

import gzip
import os
import sys
import struct

sys.path.append("/home/norgeot/dev/own/FaciLe/projects/tools/")
import msh

"""
http://www.clintons3d.com/plugins/downloads/read_blender_fluids.py
"""

fvectorFMT = 'fff'


if __name__=="__main__":
    inputDir = "/home/norgeot/Desktop/cachefluids"
    outputFile = "/home/norgeot/Desktop/cachefluids/test.mesh"
    mesh = msh.Mesh()
    
    inputBobjFiles = [os.path.join(inputDir,f) for f in os.listdir(inputDir) if ".bobj.gz" in f]
    inputFile = inputBobjFiles[0]

    print inputFile

    f = gzip.open(inputFile, 'rb', 1)
    recordSize = struct.calcsize('i')

    #Reading the vertices size
    record = f.read(recordSize)
    if len(record) < recordSize:
        f.close()
        print 'Error End of File.'
        sys.exit()
    numVerts = int(struct.unpack('i', record)[0])
    if numVerts == 0:
        f.close()
        print 'Zero vertices found.  Skip frame.'
        sys.exit()
    print recordSize, numVerts

    #Reading the vertices
    verts = []
    coordsSize = struct.calcsize('fff')
    print coordsSize
    for i in range(numVerts):
        record = f.read(coordsSize)
        if len(record) < coordsSize:
            f.close()
            print 'Error End of File.'
            sys.exit()            
        xstring, ystring, zstring = struct.unpack('fff', record)
        vert = [-float(xstring), float(ystring), float(zstring)]
        verts.append(vert)
    mesh.verts = msh.np.c_[ verts, msh.np.ones(numVerts) ]

    #Pass the normals
    norms = []
    recordSize = struct.calcsize('i')
    record = f.read(recordSize)
    if len(record) < recordSize:
        f.close()
        print 'Error End of File.'
        sys.exit()
    numNormals = int(struct.unpack('i', record)[0])
    recordSize = struct.calcsize('fff')
    for i in range(numNormals):
        record = f.read(recordSize)
        if len(record) < recordSize:
            f.close()
            print 'Error End of File.'
            sys.exit()
        xstring, ystring, zstring = struct.unpack("fff", record)
        normals = [-float(xstring), float(ystring), float(zstring)]
        norms.append(normals)
    #mesh.normals = msh.np.array(norms)
    print "last normal: ", normals

    
    # Read the triangles
    tris = []
    recordSize = struct.calcsize('i')
    record = f.read(recordSize)
    if len(record) < recordSize:
        f.close()
        print 'Error End of File.'
        sys.exit()
    numTris = int(struct.unpack('i', record)[0])
    
    recordSize = struct.calcsize("fff")
    for i in range(numTris):
        record = f.read(recordSize)
        if len(record) < recordSize:
            f.close()
            print 'Error End of File.'
            sys.exit()
        istring, jstring, kstring = struct.unpack("iii", record)
        tri = [int(istring), int(jstring), int(kstring)]
        tris.append(tri)

    mesh.tris = msh.np.c_[ tris, msh.np.ones(numTris) ]
    print "last tri: ", tri
    f.close()

    #Write the .mesh
    mesh.write(outputFile)

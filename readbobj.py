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


def readBobj(path):
    f = gzip.open(path, 'rb', 1)
    recordSize = struct.calcsize('i')

    #Reading the vertices size
    record = f.read(struct.calcsize('i'))
    if len(record) < struct.calcsize('i'):
        f.close()
        print 'Error End of File.'
        sys.exit()
    numVerts = int(struct.unpack('i', record)[0])
    if numVerts == 0:
        f.close()
        print 'Zero vertices found.  Skip frame.'
        sys.exit()
    #Reading the vertices
    verts = []
    coordsSize = struct.calcsize('fff')
    for i in range(numVerts):
        record = f.read(coordsSize)
        if len(record) < coordsSize:
            f.close()
            print 'Error End of File.'
            sys.exit()            
        xstring, ystring, zstring = struct.unpack('fff', record)
        vert = [-float(xstring), float(ystring), float(zstring)]
        verts.append(vert)
    
    #Read the normals
    norms = []
    record = f.read(struct.calcsize('i'))
    if len(record) < struct.calcsize('i'):
        f.close()
        print 'Error End of File.'
        sys.exit()
    numNormals = int(struct.unpack('i', record)[0])
    for i in range(numNormals):
        record = f.read(struct.calcsize('fff'))
        if len(record) < struct.calcsize('fff'):
            f.close()
            print 'Error End of File.'
            sys.exit()
        xstring, ystring, zstring = struct.unpack("fff", record)
        normals = [-float(xstring), float(ystring), float(zstring)]
        norms.append(normals)
    
    # Read the triangles
    tris = []
    recordSize = struct.calcsize('i')
    record = f.read(recordSize)
    if len(record) < recordSize:
        f.close()
        print 'Error End of File.'
        sys.exit()
    numTris = int(struct.unpack('i', record)[0])
    for i in range(numTris):
        record = f.read(struct.calcsize("iii"))
        if len(record) < struct.calcsize("iii"):
            f.close()
            print 'Error End of File.'
            sys.exit()
        istring, jstring, kstring = struct.unpack("iii", record)
        tri = [int(istring), int(jstring), int(kstring)]
        tris.append(tri)

    f.close()
    
    return verts, norms, tris

def writeBobj(path, verts, normals, tris):
     with gzip.open(path, 'wb', 1) as f:
        string = struct.pack("i", len(verts))
        f.write(string)
        for v in verts:
            string=struct.pack("fff", v[0], v[1], v[2])
            f.write(string)

        string = struct.pack("i", len(normals))
        f.write(string)
        for n in normals:
            string=struct.pack("fff", n[0], n[1], n[2])
            f.write(string)

        string = struct.pack("i", len(tris))
        f.write(string)
        for t in tris:
            string=struct.pack("iii", t[0], t[1], t[2])
            f.write(string)
            
def writeBvel(path):
    pass
def readBvel(path):
    pass
    #return vels


if __name__=="__main__":
    
    path       = "/home/norgeot/Desktop/cachefluids"

    inputBobjs = [os.path.join(path,f) for f in os.listdir(path) if ".bobj.gz" in f]
    inputBvels = [os.path.join(path,f) for f in os.listdir(path) if ".bvel.gz" in f]
    
    for bobj in inputBobjs:
        verts, normals, tris = readBobj(bobj)
        #vels                 = readBvel(inputBvels[0]) 
        
        #Write a .mesh
        """
        mesh = msh.Mesh()
        mesh.verts    = msh.np.c_[ verts,   msh.np.ones(len(verts)) ]
        mesh.tris     = msh.np.c_[ tris,    msh.np.ones(len(tris)) ]
        mesh.normals  = msh.np.c_[ normals, msh.np.ones(len(normals)) ]
        mesh.write( os.path.join(path, "test.mesh") )
        """

        #ReWrite a new .bobj file from the data
        outBobj = "/home/norgeot/Desktop/cachefluids/test/" + bobj.split("/")[-1]
        writeBobj(outBobj, verts, normals, tris)
        
        
        """
        #read them back to make sure the files are the same
        verts2, normals2, tris2 = readBobj(outBobj)
        print len(verts),  len(normals),  len(tris)
        print len(verts2), len(normals2), len(tris2)
        """

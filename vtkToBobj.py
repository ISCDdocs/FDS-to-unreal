"""
Reads in a .bobj file from blender cache files (fluid simulation), in order to overwrite it with FDS results
"""

import gzip
import os
import sys
import struct
import numpy as np

sys.path.append("/home/norgeot/dev/own/FaciLe/projects/tools/")
import msh

"""
http://www.clintons3d.com/plugins/downloads/read_blender_fluids.py
"""

def vtkToBobj(vtkFilePath, bobjFilePath):
    with open(vtkFilePath) as vtkIn:
        #with gzip.open(bobjFilePath, 'wb', 1) as bobjOut:
        with open("test.mesh",'w') as bobjOut:
            lines = [l.strip() for l in vtkIn.readlines()]
            dims  = [int(x) for x in lines[4].split()[1:]]
            print dims

            #Faudra mettre a l'echelle

            #Get the starting point
            start = None
            for i,l in enumerate(lines):
                if "LOOKUP_TABLE" in l:
                    start = i+1
                    break

            #Read in the values
            vals = []
            ind  = start
            for l in lines[start:]:
                lineValues = [ int(x) for x in l.split() ]
                vals+=lineValues
            print len(vals)

            #Create the squares when there is a value > specified
            isovalue = 225
            grid = np.reshape(vals, (dims[2], dims[1], dims[0]))
            cubeVerts = []
            cubeTris  = []
            cubeVals  = []

            #For the moment, write a xyz file
            for i in range(grid.shape[0]):
                for j in range(grid.shape[1]):
                    for k in range(grid.shape[2]):
                        if grid[i,j,k]>isovalue:
                            #create a cube
                            s = 0.5
                            tmp = msh.Mesh(cube=[i-s, i+s, j-s, j+s, k-s, k+s])

                            for t in tmp.tris:
                                offset = len(cubeVerts)
                                cubeTris.append([ t[0]+offset, t[1]+offset, t[2]+offset, t[3] ])
                            for v in tmp.verts:
                                cubeVerts.append(v)

                            for z in range(8):
                                cubeVals.append(grid[i,j,k])

            mesh = msh.Mesh()
            mesh.verts = np.array(cubeVerts)
            mesh.tris = np.array(cubeTris)
            mesh.scalars = np.array(cubeVals)

            print len(mesh.verts), len(mesh.tris)
            mesh.write("toto.mesh")
            mesh.writeSol("toto.sol")
            #bobjOut.write("%i %i %i\n" % (i,j,k))
            #
        """
            #Read the vtk properties
            for l in f.readlines():
                if l.split()[0] == "DIMENSIONS":
                    dims = [int(x) for x in l.strip()split()[1:]]
                    break


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
        """


if __name__=="__main__":
    vtkToBobj("/home/norgeot/Desktop/Fires/vtk/room_fire_SOOT_701.vtk", "/home/norgeot/toto.bobj.gz")

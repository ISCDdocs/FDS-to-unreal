# coding: utf8

import sys
sys.path.append("/home/norgeot/dev/own/FaciLe/projects/tools/")
import msh

import scipy.interpolate
import numpy as np

def read(f):
    mesh = msh.Mesh(f)
    mesh.readSol()
    mesh.caracterize()
    return mesh

if __name__=="__main__":
    if len(sys.argv) == 1:
        sys.exit()

    #On lit le fichier
    mesh = read(sys.argv[1])

    #On inverse
    mesh.verts[:,1]*=-1
    temp = np.copy(mesh.verts[:,0])
    mesh.verts[:,0] = mesh.verts[:,2]
    mesh.verts[:,2] = temp
    
    mesh.computeBBox()
    
    
    #Les coordonnées des points shape (n,D)
    points = mesh.verts[:,:3]
    vectors = mesh.vectors
    del mesh

    #Pour avoir moins de données
    #points = points[::5]
    #vectors = vectors[::5]
    
    xmin, xmax = np.min(points[:,0]), np.max(points[:,0])
    ymin, ymax = np.min(points[:,1]), np.max(points[:,1])
    zmin, zmax = np.min(points[:,2]), np.max(points[:,2])

    #La grille sur laquelle on va interpoler
    res = 64
    xi = []
    for x in np.arange(xmin, xmax, (xmax-xmin)/res):
        for y in np.arange(ymin, ymax, (ymax-ymin)/res):
            for z in np.arange(zmin, zmax, (zmax-zmin)/res):
                xi.append(x)
                xi.append(y)
                xi.append(z)

    vX = scipy.interpolate.griddata(points, vectors[:,0], xi, fill_value=0)
    vY = scipy.interpolate.griddata(points, vectors[:,1], xi, fill_value=0)
    vZ = scipy.interpolate.griddata(points, vectors[:,2], xi, fill_value=0)

    with open("/home/norgeot/theatre_fga.fga","w") as f:
        f.write(str(res) + "," + str(res) + "," + str(res) + ",\n")
        f.write("%.8f,%.8f,%.8f,\n" % (100*zmin,100*ymin,100*xmin))
        f.write("%.8f,%.8f,%.8f,\n" % (100*zmax,100*ymax,100*xmax))
        for x,y,z in zip(vX, vY, vZ):
            f.write("%.8f,%.8f,%.8f," % (x,-y,z))

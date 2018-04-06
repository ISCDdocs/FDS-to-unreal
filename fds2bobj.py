import vtk
import numpy as np
import os
import sys
sys.path.append("/home/norgeot/dev/own/pythonMesh/src/")
import msh
import argparse
import gzip
import struct

"""
python fds2ascii.py --input Desktop/Fires/ -o Desktop/Fires/vtk/ --start 700 --end 750 --run

pb: permettre plusieurs etapes:
1. exporter de la donnée fds vers vtk pour lire en paraview
2. mise au point du filtre paraview ou en vtk
3. Incorporer le filtre vtk dans le code python
4. préparer la simulation en blender
5. modifier les fichiers de cache de blender
"""

def getGridFromSMV(path):
    with open(path) as f:
        lines = [l.strip() for l in f.readlines()]
        lines = [l for l in lines if l!=""]
    #Get the begin
    begin = [0,0,0]
    for i,l in enumerate(lines):
        for j,kwd in enumerate(["TRNX", "TRNY", "TRNZ"]):
            if kwd in l:
                begin[j] = i+2
    #Write the X, Y and Z coords
    currentInd = 0
    X, Y, Z = [], [], []
    for i,l in enumerate(lines):
        if i>=begin[currentInd]:
            try:
                if currentInd==0:
                    X.append(float(l.split()[1]))
                if currentInd==1:
                    Y.append(float(l.split()[1]))
                if currentInd==2:
                    Z.append(float(l.split()[1]))
            except:
                if currentInd == 2:
                    break
                else:
                    currentInd+=1
    print(len(X), len(Y), len(Z))
    return X,Y,Z
def getOutputFilesFromSMV(path):
    with open(path) as f:
        files = []
        lines = [l.strip() for l in f.readlines()]
        lines = [l for l in lines if l!=""]
        for i in range(len(lines)):
            if lines[i].split()[0]=="SMOKF3D":
                files.append([lines[i+2].split()[0], lines[i+1].strip()])
            if lines[i].split()[0]=="SLCF":
                files.append([lines[i+2].strip(), lines[i+1].strip()])
        return files
def toInt(byte):
    return int(byte.encode('hex'), 16)
def readS3D(s3dfile, frames, start=0, end=None):
    if end is None:
        end = len(frames)

    VALUES = []
    with open(s3dfile, "rb") as f:
        #First offset
        X = 36
        f.seek(X,1)

        #Skipping until the start
        for frame in frames[:start]:
            f.seek(72-X, 1)
            f.seek(int(frame[2]), 1)

        #Reading from start to end
        if start!=0 or end!=len(frames):
            print "Reading the frames " + str(start) + " to " + str(end)
        for ind, frame in enumerate(frames[start:end]):
            f.seek(72-X, 1)
            bits  = f.read(int(frame[2]))
            vals  = []
            i     = 0
            while(i<len(bits)):
                if toInt(bits[i]) == 255:
                    val = toInt(bits[i+1])
                    n   = toInt(bits[i+2])
                    for j in range(n):
                        vals.append(val)
                    i+=3
                else:
                    val = toInt(bits[i])
                    vals.append(val)
                    i+=1
            VALUES.append(vals)
    return VALUES
def writeVTKArray(arr, header, f):
    f.write(header)
    for i in range(len(arr)/6 + 1):
        for j in range(6):
            if 6*i + j < len(arr):
                f.write(str(arr[6*i + j]) + " ")
        f.write("\n")
def exportVTK(filepath, name, x,y,z,values):
    with open(filepath, "w") as f:
        f.write("# vtk DataFile Version 2.0\nSample rectilinear grid\nASCII\nDATASET RECTILINEAR_GRID\n")
        f.write("DIMENSIONS " + " ".join([str(len(_tmp)) for _tmp in [x,y,z]]) + "\n")
        writeVTKArray(x, "X_COORDINATES " + str(len(x)) + " float\n", f)
        writeVTKArray(y, "Y_COORDINATES " + str(len(y)) + " float\n", f)
        writeVTKArray(z, "Z_COORDINATES " + str(len(z)) + " float\n", f)
        writeVTKArray(values, "POINT_DATA " + str(len(values)) + "\nSCALARS " + name + " float\nLOOKUP_TABLE default\n", f)
def arguments():
    parser = argparse.ArgumentParser(description='Converts FDS outputs to vtk.')
    parser.add_argument('--input',   '-i', help='simulation root path', required=True)
    parser.add_argument('--run',     '-r', help='really run', action="store_true", default=False)
    parser.add_argument('--output',  '-o', help='output folder (default to input folder)')
    parser.add_argument('--start',   '-s', help='frame to start extraction (default to first)', type=int, default=0)
    parser.add_argument('--end',     '-e', help='frame to end extraction (default to last available)', type=int, default=0)
    args = parser.parse_args()

    if not os.path.isdir(args.input):
        print args.input + " not a directory"
        sys.exit()
    if len([f for f in os.listdir(args.input) if f[-4:]==".smv"])==0:
        print "No .smv file in " + args.input
        sys.exit()
    args.input = os.path.abspath(args.input)

    if args.output is not None:
        if not os.path.isdir(args.output):
            print args.output + " does not exist, please create it"
            sys.exit()
    else:
        args.output = args.input
    args.output = os.path.abspath(args.output)

    return args

def doSomething(rgrid, value, outFile):
    # Fill the value array
    signedDistances = vtk.vtkFloatArray()
    signedDistances.SetNumberOfComponents(1)
    signedDistances.SetName("SignedDistances")
    for v in value:
        signedDistances.InsertNextValue(v)

    # Add the value array to the grid
    rgrid.GetPointData().SetScalars(signedDistances)

    # Extract the isosurface
    iso = vtk.vtkContourFilter()
    iso.SetInputData(rgrid)
    iso.SetNumberOfContours(1)
    iso.SetValue(0,40)
    iso.Update()

    #Get verts and triangles
    polydata = iso.GetOutput()
    verts     = np.array([ [polydata.GetPoint(i)[j] if j<3 else 0 for j in range(4)] for i in range(polydata.GetNumberOfPoints()) ])
    tris      = np.array([ [polydata.GetCell(i).GetPointIds().GetId(j) if j<3 else 0 for j in range(4)] for i in range(polydata.GetNumberOfCells()) ])

    #Write a .bobj file
    with gzip.open(outFile, "wb") as f:
        string = struct.pack("i", len(verts))
        f.write(string)
        for v in verts:
            string=struct.pack("fff", v[0], v[1], v[2])
            f.write(string)
        string = struct.pack("i", len(verts))
        f.write(string)
        for n in verts:
            string=struct.pack("fff", n[0], n[1], n[2])
            f.write(string)
        string = struct.pack("i", len(tris))
        f.write(string)
        for t in tris:
            string=struct.pack("iii", t[0], t[1], t[2])
            f.write(string)

if __name__=="__main__":
    # 0 - Argument parsing
    args = arguments()
    case = [f[:-4] for f in os.listdir(args.input) if f[-4:]==".smv"][0]

    # 1 - Get the grid info
    _x,_y,_z = getGridFromSMV(os.path.join(args.input, case + ".smv"))
    # The vtk part
    xCoords = vtk.vtkFloatArray()
    for i in _x:
        xCoords.InsertNextValue(i)
    yCoords = vtk.vtkFloatArray()
    for i in _y:
        yCoords.InsertNextValue(i)
    zCoords = vtk.vtkFloatArray()
    for i in _z:
        zCoords.InsertNextValue(i)
    rgrid = vtk.vtkRectilinearGrid()
    rgrid.SetDimensions(len(_x), len(_y), len(_z))
    rgrid.SetXCoordinates(xCoords)
    rgrid.SetYCoordinates(yCoords)
    rgrid.SetZCoordinates(zCoords)



    # 2 - Get the output data files (.s3d and .sf)
    files = getOutputFilesFromSMV(os.path.join(args.input, case + ".smv"))

    # 3 - Loop on the data files
    if args.run:
        for f in files[1:]:

            #Read the .s3d files
            if f[1][-4:] == ".s3d":
                with open( os.path.join(args.input, f[1] + ".sz") ) as fsz:
                    frames = np.array([[float(x) for x in l.split()] for l in fsz.readlines()[1:]])
                if args.start > len(frames):
                    print str(args.start) + " > nFrames (" + str(len(frames)) + ")!"
                    sys.exit()
                if args.end!=0:
                    if args.end<args.start:
                        print "end frame must be > start frame"
                        sys.exit()
                    if args.end>len(frames):
                        print str(args.end) + " > nFrames (" + str(len(frames)) + ")!"
                        sys.exit()
                else:
                    args.end = len(frames)

                values = readS3D( os.path.join(args.input,f[1]) , frames , args.start, args.end)

                #Don't write to vtk!!!
                for i,v in enumerate(values):
                    #vtkFile = os.path.join(args.output, case + "_" + f[0] + "_" + str(args.start + i + 1) + ".vtk")
                    #print "Writing " + vtkFile
                    #exportVTK(vtkFile , f[0], _x, _y, _z, v )
                    doSomething(rgrid, v, os.path.join("/home/norgeot/Desktop/cachefluids/test/cache_fluid/cache_fluid", "fluidsurface_preview_" + str(i).zfill(4) + ".bobj.gz") )

    else:
        print args
        print case
        print len(_x), len(_y), len(_z)
        for f in files:
            print f
        print "To run the script, add the --run option"




    #write a .mesh file
    """
    mesh = msh.Mesh()
    mesh.verts = verts
    mesh.tris  = triangles
    mesh.write("toto.mesh")
    """

    """
        cell = polydata.GetCell(i)
        for j in range(cell.GetNumberOfFaces()):
            print "toto"
            face = cell.GetFace(i)
            print face
        #face = polydata.GetFace(i)#only triangles
        #print face.GetPointIds()
    """

    """

    rgridMapper = vtk.vtkPolyDataMapper()
    rgridMapper.SetInputConnection(iso.GetOutputPort())



    wireActor = vtk.vtkActor()
    wireActor.SetMapper(rgridMapper)
    wireActor.GetProperty().SetRepresentationToWireframe()
    wireActor.GetProperty().SetColor(0, 0, 0)

    # Create the usual rendering stuff.
    renderer = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    renderer.AddActor(wireActor)
    renderer.SetBackground(0,0,0)
    renderer.ResetCamera()
    renderer.GetActiveCamera().Elevation(60.0)
    renderer.GetActiveCamera().Azimuth(30.0)
    renderer.GetActiveCamera().Zoom(1.0)

    renWin.SetSize(300, 300)

    # interact with data
    renWin.Render()
    iren.Start()
    """

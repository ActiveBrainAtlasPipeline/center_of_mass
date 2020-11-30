### Building the Active Brain Atlas
##### Fetching data
1. The data for the Active Brain Atlas is stored as two sets of numpy arrays. One set contains the actual
numpy array volume and the other set contains the 3 x,y,z coordinates in a text file. (There is another set of STL
files, but that is only for importing into 3D Slicer and that will be discussed below.)
1. Get the sets of data from Amazon S3. Each zip file contains 51 files. There are 3 zip files:
    1. structures.zip - this is the set of numpy arrays
    1. origin.zip this is the set of origin files containing the x,y,z coordinates.
    1. mesh.zip this is the set of mesh stl files for 3D Slicer
1. Download each file with:
    1. aws s3 cp s3://mousebrainatlas-data/atlasV7/origin.zip origin.zip
    1. aws s3 cp s3://mousebrainatlas-data/atlasV7/structures.zip structures.zip
    1. aws s3 cp s3://mousebrainatlas-data/atlasV7/mesh.zip mesh.zip
1. After downloading the zip files, unzip them and you will have 3 new directories containing the 51 files.


#### Building for 3D Slicer
1. After unzipping the mesh.zip file, you will have a new directory called 'mesh'. Simply import all the stl files
into 3D Slicer as models. It is best to choose the '3D only' layout.


#### Building for Neuroglancer
1. To build the atlas for neuroglancer you will also need an existing stack of images to get the centers of mass. 
This can be done by opening your stack in neuroglancer, find at least 3 structures in your stack that correspond
to the structures found in the structures.zip file and then get the center of mass, x,y,z coordinates for those 
structures. Copy the data into a python dictionary similar to this:
`com_data = {'SC':[40000, 30000, 0], '7n_R':[45000,35000, 300], '7n_L':[45000, 35000, 1000]}`
1. The origin files you download above each contain a x,y,z set of coordinates. These coordinates represent
the distance in 10um units each structure is away from the center of a virtual 3D space. The scripts provided
with this install will help in converting the units of the atlas to the units in your image stack.
1. Get the python scripts

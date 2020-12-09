## Building and aligning the Active Brain Atlas
#### Fetching data
1. The data for the Active Brain Atlas is stored as two sets of numpy arrays. One set contains the actual
numpy array volume and the other set contains the 3 x,y,z coordinates in a text file. (There is another set of STL
files, but that is only for importing into 3D Slicer and that will be discussed below.)
<!-- 1. Get the sets of data from Amazon S3. Each zip file contains 51 files. There are 3 zip files:
    1. structures.zip - this is the set of numpy arrays
    1. origin.zip this is the set of origin files containing the x,y,z coordinates.
    1. mesh.zip this is the set of mesh stl files for 3D Slicer -->
<!-- 1. Download each file with:
    1. `aws s3 cp s3://mousebrainatlas-data/atlasV7/origin.zip origin.zip`
    1. `aws s3 cp s3://mousebrainatlas-data/atlasV7/structures.zip structures.zip`
    1. `aws s3 cp s3://mousebrainatlas-data/atlasV7/mesh.zip mesh.zip` -->
1. Download the Atlas data by running either of the following commands
```Bash
curl https://activebrainatlas.ucsd.edu/atlasV7.tar.gz | tar -xz
wget -O- https://activebrainatlas.ucsd.edu/atlasV7.tar.gz | tar -xz
```
<!-- 1. After downloading the zip files, unzip them and you will have 3 new directories containing the 51 files. -->
1. You should now have a directory atlasV7 with 3 sub-directories, each containing 51 files.
    - `structures` - the set of numpy arrays
    - `origin` - the set of origin files containing the x,y,z coordinates
    - `mesh` - the set of mesh stl files for 3D Slicer

#### Building for 3D Slicer
1. Simply import all the stl files in the `mesh` sub-folder into 3D Slicer as models. It is best to choose the '3D only' layout.

#### Building the atlas and importing into Neuroglancer
1. You will need the structures and the origin files on your local file system. The two folder should be in the `atlasV7` folder you just downloaded.
1. You will need git, python3-pip and python3-venv (recommended) to run the scripts. Run the following to generate precomputed file-backed datasource for neuroglancer.

Please ensure that your current folder contains the `atlasV7` folder as our script assumes that. For atlas stored elsewhere, please change `atlas_dir` variable in `create_atlas.py` and `center_of_mass.py`.
```Bash
sudo apt-get install git python3-pip python3-venv
# Clone the python scripts from this repository
git clone git@github.com:ActiveBrainAtlasPipeline/center_of_mass.git && cd center_of_mass
# Create a virtual environment (highly recommended)
python3 -m venv ~/.virtualenvs/center_of_mass
source ~/.virtualenvs/center_of_mass/bin/activate
# update pip
pip install -U pip
# Install required python libraries
pip install -r requirements.txt
# Install igneous
git clone https://github.com/seung-lab/igneous.git && cd igneous && python setup.py install && cd ..
# Build the atlas in neuroglancer format
python create_atlas.py
```
1. The default output directory is `atlas_ng` outside the `center_of_mass` folder.
1. Copy that directory to location accessible by your web server.
1. Open neuroglancer. In the source tab, input `precomputed://https:{PATH_TO_ATLAS_IN_YOUR_SERVER}`.
1. Click the button `Create as segmentation layer` on the bottom right corner if the layer does not show up.
1. The atlas should show up as a new layer. (To show the volume in the 3rd quadrant, go to the `Seg.` tab on the top right corner and click the segments).

#### Aligning the atlas for Neuroglancer
1. To align the atlas in Neuroglancer you will also need an existing stack of images to get the centers of mass. 
This can be done by opening your stack in neuroglancer, find at least 3 structures in your stack that correspond
to the structures found in the structures.zip file and then get the center of mass, x,y,z coordinates for those 
structures. Copy the data into a python dictionary similar to this:
```
reference_centers = {'SC':[40000, 30000, 0], '7N_R':[45000,35000, 300], '7N_L':[45000, 35000, 1000]}
```
1. The origin files you download above each contain a x,y,z set of coordinates. These coordinates represent
the distance in 10um units each structure is away from the center of a virtual 3D space. The scripts provided
with this install will help in converting the units of the atlas to the units in your image stack.
1. open up the file: center_of_mass.py and add your python dictionary to the main method at the bottom the file. 
1. now, simply run the program `python center_of_mass.py`
1. The program will print out the rotation matrix and the translation vector. Copy the 3x3 rotation matrix 
into the layer's source matrix and the vector into the layer's translation vector.
1. The atlas should align with the image stack.

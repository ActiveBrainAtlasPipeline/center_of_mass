import os
from skimage import measure
import cv2
import json

import numpy as np
import neuroglancer
import tinybrain
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume

RESOLUTION = 0.325 # change this if needed


def get_db_structure_infos():
    db_structures = {'10N_L': ['Dorsal nucleus of vagus nerve', 1],
     '10N_R': ['Dorsal nucleus of vagus nerve', 1],
     '12N': ['Hypoglossal nucleus', 2],
     '3N_L': ['Oculomotor nucleus', 3],
     '3N_R': ['Oculomotor nucleus', 3],
     '4N_L': ['Trochlear nucleus', 4],
     '4N_R': ['Trochlear nucleus', 4],
     '5N_L': ['Trigeminal motor nucleus', 5],
     '5N_R': ['Trigeminal motor nucleus', 5],
     '6N_L': ['Abducens nucleus', 6],
     '6N_R': ['Abducens nucleus', 6],
     '7N_L': ['Facial nucleus', 7],
     '7N_R': ['Facial nucleus', 7],
     '7n_L': ['Facial nerve', 9],
     '7n_R': ['Facial nerve', 9],
     'AP': ['Area postrema', 28],
     'Amb_L': ['Nucleus ambiggus', 8],
     'Amb_R': ['Nucleus ambiggus', 8],
     'DC_L': ['Dorsal cochlea nucleus', 10],
     'DC_R': ['Dorsal cochlea nucleus', 10],
     'IC': ['Inferior colliculus', 11],
     'LC_L': ['Locus corelus', 12],
     'LC_R': ['Locus corelus', 12],
     'LRt_L': ['Lateral reticular nucleus', 13],
     'LRt_R': ['Lateral reticular nucleus', 13],
     'PBG_L': ['Parabigeminal nucleus', 14],
     'PBG_R': ['Parabigeminal nucleus', 14],
     'Pn_L': ['Pontine grey', 15],
     'Pn_R': ['Pontine grey', 15],
     'R': ['Red nucleus', 16],
     'RtTg': ['Reticulotegmental nucleus', 17],
     'SC': ['Superior colliculus', 18],
     'SNC_L': ['Substantia niagra, compact', 19],
     'SNC_R': ['Substantia niagra, compact', 19],
     'SNR_L': ['Substantia niagra, reticular', 20],
     'SNR_R': ['Substantia niagra, reticular', 20],
     'Sp5C_L': ['Spinal-trigeminal nucleus, caudalis', 21],
     'Sp5C_R': ['Spinal-trigeminal nucleus, caudalis', 21],
     'Sp5I_L': ['Spinal-trigeminal nucleus, interpolaris', 22],
     'Sp5I_R': ['Spinal-trigeminal nucleus, interpolaris', 22],
     'Sp5O_L': ['Spinal-trigeminal nucleus, oralis', 23],
     'Sp5O_R': ['Spinal-trigeminal nucleus, oralis', 23],
     'Tz_L': ['Nucleus of trapezoidal body', 24],
     'Tz_R': ['Nucleus of trapezoidal body', 24],
     'VCA_L': ['Ventral cochlea nucleus, anterior', 25],
     'VCA_R': ['Ventral cochlea nucleus, anterior', 25],
     'VCP_L': ['Ventral cochlea nucleus, posterior', 26],
     'VCP_R': ['Ventral cochlea nucleus, posterior', 26],
     'VLL_L': ['Ventral lateral lemniscus', 27],
     'VLL_R': ['Ventral lateral lemniscus', 27]}
    return db_structures

def get_known_foundation_structure_names():
    known_foundation_structures = ['MVePC', 'DTgP', 'VTA', 'Li', 'Op', 'Sp5C', 'RPC', 'MVeMC', 'APT', 'IPR',
                                   'Cb', 'pc', 'Amb', 'SolIM', 'Pr5VL', 'IPC', '8n', 'MPB', 'Pr5', 'SNR',
                                   'DRD', 'PBG', '10N', 'VTg', 'R', 'IF', 'RR', 'LDTg', '5TT', 'Bar',
                                   'Tz', 'IO', 'Cu', 'SuVe', '12N', '6N', 'PTg', 'Sp5I', 'SNC', 'MnR',
                                   'RtTg', 'Gr', 'ECu', 'DTgC', '4N', 'IPA', '3N', '7N', 'LC', '7n',
                                   'SC', 'LPB', 'EW', 'Pr5DM', 'VCA', '5N', 'Dk', 'DTg', 'LVe', 'SpVe',
                                   'MVe', 'LSO', 'InC', 'IC', 'Sp5O', 'DC', 'Pn', 'LRt', 'RMC', 'PF',
                                   'VCP', 'CnF', 'Sol', 'IPL', 'X', 'AP', 'MiTg', 'DRI', 'RPF', 'VLL']
    return known_foundation_structures




def get_structure_number(structure):
    db_structure_infos = get_db_structure_infos()
    known_foundation_structure_names = get_known_foundation_structure_names()
    non_db_structure_names = [structure for structure in known_foundation_structure_names if structure not in db_structure_infos.keys()]

    if structure in db_structure_infos:
        color = db_structure_infos[structure][1]
    elif structure in non_db_structure_names:
        color = len(db_structure_infos) + non_db_structure_names.index(structure) + 1
    else:
        color = 255
    return color

def get_segment_properties(all_known=False):
    db_structure_infos = get_db_structure_infos()
    known_foundation_structure_names = get_known_foundation_structure_names()
    non_db_structure_names = [structure for structure in known_foundation_structure_names if structure not in db_structure_infos.keys()]

    segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
    if all_known:
        segment_properties += [(len(db_structure_infos) + index + 1, structure) for index, structure in enumerate(non_db_structure_names)]

    return segment_properties



class NumpyToNeuroglancer():
    viewer = None

    def __init__(self, volume, scales, offset=[0, 0, 0], layer_type='segmentation'):
        self.volume = volume
        self.scales = scales
        self.offset = offset
        self.layer_type = layer_type

        self.precomputed_vol = None

    def preview(self, layer_name=None, clear_layer=False):
        if self.viewer is None:
            self.viewer = neuroglancer.Viewer()

        if layer_name is None:
            layer_name = f'{self.layer_type}_{self.scales}'

        source = neuroglancer.LocalVolume(
            data=self.volume,
            dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='nm', scales=self.scales),
            voxel_offset=self.offset
        )

        if self.layer_type == 'segmentation':
            layer = neuroglancer.SegmentationLayer(source=source)
        else:
            layer = neuroglancer.ImageLayer(source=source)

        with self.viewer.txn() as s:
            if clear_layer:
                s.layers.clear()
            s.layers[layer_name] = layer

        print(f'A new layer named {layer_name} is added to:')
        print(self.viewer)

    def init_precomputed(self, path):
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[3] if len(self.volume.shape) > 3 else 1,
            layer_type = self.layer_type,
            data_type = str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',                    # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset,          # x,y,z offset in voxels from the origin
            chunk_size = [64, 64, 64],           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=False, progress=False)
        self.precomputed_vol.commit_info()
        self.precomputed_vol[:, :, :] = self.volume[:, :, :]

    def add_segment_properties(self, segment_properties):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        self.precomputed_vol.info['segment_properties'] = 'names'
        self.precomputed_vol.commit_info()

        segment_properties_path = os.path.join(self.precomputed_vol.layer_cloudpath.replace('file://', ''), 'names')
        os.makedirs(segment_properties_path, exist_ok=True)

        info = {
            "@type": "neuroglancer_segment_properties",
            "inline": {
                "ids": [str(number) for number, label in segment_properties],
                "properties": [{
                    "id": "label",
                    "type": "label",
                    "values": [str(label) for number, label in segment_properties]
                }]
            }
        }
        with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
            json.dump(info, file, indent=2)

    def add_downsampled_volumes(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        tq = LocalTaskQueue(parallel=1)
        tasks = tc.create_downsampling_tasks(self.precomputed_vol.layer_cloudpath, compress=False)
        tq.insert(tasks)
        tq.execute()

    def add_segmentation_mesh(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        tq = LocalTaskQueue(parallel=1)
        tasks = tc.create_meshing_tasks(self.precomputed_vol.layer_cloudpath, mip=0, compress=False) # The first phase of creating mesh
        tq.insert(tasks)
        tq.execute()

        # It should be able to incoporated to above tasks, but it will give a weird bug. Don't know the reason
        tasks = tc.create_mesh_manifest_tasks(self.precomputed_vol.layer_cloudpath) # The second phase of creating mesh
        tq.insert(tasks)
        tq.execute()


def mask_to_shell(mask):
    sub_contours = measure.find_contours(mask, 1)

    sub_shells = []
    for sub_contour in sub_contours:
        sub_contour.T[[0, 1]] = sub_contour.T[[1, 0]]
        pts = sub_contour.astype(np.int32).reshape((-1, 1, 2))

        sub_shell = np.zeros(mask.shape, dtype='uint8')
        sub_shell = cv2.polylines(sub_shell, [pts], True, 1, 5, lineType=cv2.LINE_AA)
        sub_shells.append(sub_shell)
    shell = np.array(sub_shells).sum(axis=0)
    del sub_shells
    return shell

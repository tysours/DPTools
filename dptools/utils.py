"""
Assorted utilities for plots, reading things, converting things, etc.
"""
import numpy as np
from ase import Atoms
from ase.io import write, read
from ase.io.formats import string2index
from ase.db import connect
from ase.data import chemical_symbols
import json

#seaborn.color_palette('deep')
colors = [(0.2980392156862745, 0.4470588235294118, 0.6901960784313725),
          (0.8666666666666667, 0.5176470588235295, 0.3215686274509804),
          (0.3333333333333333, 0.6588235294117647, 0.40784313725490196),
          (0.7686274509803922, 0.3058823529411765, 0.3215686274509804),
          (0.5058823529411764, 0.4470588235294118, 0.7019607843137254),
          (0.5764705882352941, 0.47058823529411764, 0.3764705882352941),
          (0.8549019607843137, 0.5450980392156862, 0.7647058823529411),
          (0.5490196078431373, 0.5490196078431373, 0.5490196078431373),
          (0.8, 0.7254901960784313, 0.4549019607843137),
          (0.39215686274509803, 0.7098039215686275, 0.803921568627451)]

def _generate_color():
    for color in colors:
        yield color

_gen_color = _generate_color()
def next_color():
    """
    Convenience function to grab a new color during plotting loops.

    Returns:
        color (tuple[float]): New color rgb vals from seaborn.color_palette('deep')

    Example:

        .. code-block:: python

            for values in all_values:
                plt.plot(values, color=next_color())
    """
    return next(_gen_color)


def read_dump(dump, type_map, index=":"):
    """
    Reads in lammps dump file and returns corresponding ase.Atoms list.

    Args:
        dump (str): Path to dump file to read.
        type_map (dict): Dictionary with element-index mapping, e.g. {'Si': 0, 'O': 1}
        index (str): index slice to control which images are returned, e.g. ':', '::100', etc.

    Returns:
        traj (list[ase.Atoms]): List of dump images as ase.Atoms objects
    """
    type_map = read_type_map(type_map) # support str, json, dict inputs
    if 0 in type_map.values(): # lammps indexing starts at 1
        type_map = {k: v + 1 for k, v in type_map.items()}
    type_map = {v: k for k, v in type_map.items()} # invert to find symbol from type index
    with open(dump) as file:
        lines = file.readlines()
    traj = []
    # n_atoms = int(lines[3])
    for i, line in enumerate(lines):
        if "BOX BOUNDS" in line:
            n_atoms = int(lines[i - 1])
            lammps_cell = np.array([_str_to_float(lines[i + j + 1]) for j in range(3)])
            cell, shift = convert_dump_cell(lammps_cell)
        elif "ITEM: ATOMS" in line:
            ids = [int(l.split()[0]) for l in lines[i + 1 : i + 1 + n_atoms]]
            sort = np.argsort(ids)
            # TODO: replace index hardcodinng
            types = np.array(
                [int(l.split()[-4]) for l in lines[i + 1 : i + 1 + n_atoms]]
            )
            symbols = np.array([type_map[t] for t in types])
            positions = np.array(
                [_str_to_float(lines[i + j + 1]) for j in range(n_atoms)]
            )
            if "xs" in line:
                positions = positions @ cell
            positions = positions - shift  # shift atoms to origin for ASE Atoms object
            atoms = Atoms(
                positions=positions[sort], symbols=symbols[sort], cell=cell, pbc=True
            )
            atoms.set_tags(types[sort])
            traj.append(atoms)
    return traj[string2index(index)]


def _str_to_float(l):
    return list(map(float, l.split()[-3:]))


def convert_dump_cell(lammps_cell):
    """
    Converts lammps dump cell format to ase cell.

    Args:
        lammps_cell (numpy.array): Simulation cell from lammps dump file.

    Returns:
        cell (numpy.array): New 3x3 array to use with ase.
        shift (numpy.array): xyz shifts to place atoms at origin aligned with cell.
    """
    xlo_bound, xhi_bound = lammps_cell[0, :2]
    ylo_bound, yhi_bound = lammps_cell[1, :2]
    zlo_bound, zhi_bound = lammps_cell[2, :2]
    if lammps_cell.shape == (3, 3):
        xy, xz, yz = lammps_cell[:, -1]
    elif lammps_cell.shape == (3, 2):
        xy, xz, yz = 0.0, 0.0, 0.0

    xlo = xlo_bound - min((0.0, xy, xz, xy + xz))
    xhi = xhi_bound - max((0.0, xy, xz, xy + xz))
    ylo = ylo_bound - min((0.0, yz))
    yhi = yhi_bound - max((0.0, yz))
    zlo = zlo_bound
    zhi = zhi_bound

    a = [xhi - xlo, 0, 0]
    b = [xy, yhi - ylo, 0]
    c = [xz, yz, zhi - zlo]
    cell = np.array([a, b, c])
    shift = np.array([xlo, ylo, zlo])
    return cell, shift

def read_db(db_name, indices):
    """
    Reads ase db and returns entries as list of Atoms objects.
    Useless, just use ase.io.read(db_name, index=indices) instead.

    Args:
        db_name (str): Path to ase db file.
        indices (str): Index slice, e.g. ::10, :, 1:100, etc.

    Returns:
        traj (list[ase.Atoms]): db entries as list of Atoms objects.
    """
    with connect(db_name) as db:
        traj = [row.toatoms() for row in db.select()]
    return traj[string2index(indices)]

def graph2typemap(graph):
    """
    Determine type_map for a given deepmd model.

    Args:
        graph (str): Path to deepmd model .pb file.

    Returns:
        type_map (dict): Dictionary that maps each atomic symbol to type map index
    """
    from deepmd import DeepPotential
    dp = DeepPotential(graph)
    type_map = {sym: i for i, sym in enumerate(dp.get_type_map())}
    return type_map

def read_type_map(type_map_json):
    if isinstance(type_map_json, dict):
        type_map = type_map_json
    elif isinstance(type_map_json, str):
        if type_map_json.endswith(".json"):
            with open(type_map_json) as file:
                type_map = json.loads(file.read())
        else:
            type_map = str2typemap(type_map_json)
    else:
        if type_map_json is None:
            msg = "No default model set, try using:\tdptools set /path/to/graph.pb"
        else:
            msg = f"Unknown type_map format provided: {type_map_json}"
        raise TypeError(msg)
    return check_type_map(type_map)

def check_type_map(type_map_dict):
    # I'm inconsistent with key-value/value-key when writing type_map
    # so check if need to invert dict such that chem symbols are keys
    # TODO: fix inconsistencies
    invert = False
    for k, v in type_map_dict.items():
        if k not in chemical_symbols:
            invert = True
        break
    if invert:
        type_map_dict = {v: k for k, v in type_map_dict.items()}
    return type_map_dict

def typemap2str(type_map_dict):
    type_map = check_type_map(type_map_dict)
    tm_str = ",".join([f"{k}:{v}" for k, v in type_map.items()])
    return tm_str

def str2typemap(tm_str):
    items = tm_str.split(",")
    type_map = {i.split(":")[0]: int(i.split(":")[-1]) for i in items}
    return type_map

def randomize_seed(in_json):
    """
    Take input .json or dict with training parameters and randomize seeds
    for model ensemble training.

    Args:
        in_json (str or dict): Path to .json or dict with deepmd training parameters.

    Returns:
        (dict): Training parameter dictionary with new randomized seed values.
    """
    if isinstance(in_json, str):
        with open(in_json) as file:
            in_json = json.loads(file.read())
    elif not isinstance(in_json, dict):
        raise TypeError("Need dict or .json file to randomize seeds")
    seeds = get_seed(n=3)
    in_json["model"]["descriptor"]["seed"] = seeds[0]
    in_json["model"]["fitting_net"]["seed"] = seeds[1]
    in_json["training"]["seed"] = seeds[2]
    return in_json

def get_seed(max_val=999999, n=1):
    """
    Returns:
        seed (int or list[int]): n random ints between 0 and max_val.
    """
    if n > 1:
        seed = np.random.randint(max_val, size=n)
        seed = [int(s) for s in seed] # dtype=int64 not json serializable
    elif n == 1:
        seed = np.random.randint(max_val) # avoids single item array
    return seed

def columnize(*data):
    """
    Takes lists or 1D arrays and concatenates everything into columnized array.
    Basically just np.column_stack without needing a single tuple arg (i.e. slightly useless).
    """
    return np.array(list(data)).T

class Converter:
    """
    Class to convert between different ASE/VASP/LAMMPS outputs. Mostly useful if wanting
    to concatenate all MD images from variable-time jobs, but also supports lammps dump
    conversions and common ASE formats.

    Args:
        inputs (list[str]): Paths to input structure files to convert. Images from each
            input are concatenated in output.

        output (str): Name of file with desired conversion extension specified,
            e.g. ``'out.traj'``

        indices (str): Index slice, e.g. ``'::10'``, :, ``'1:100'``, etc.

    Example:

        .. code-block:: python

            # concat MD images (ignores 1st image if identical to final image in previous input)
            >>> from dptools.utils import Converter
            >>> inputs = ['md_000/vasprun.xml', 'md_001/vasprun.xml', 'md_002/vasprun.xml']
            >>> output = 'md.traj'
            >>> converter = Converter(inputs, outputs)
            >>> converter.convert()
    """

    def __init__(self, inputs, output, indices=":"):
        self.inputs = inputs
        self.output = output
        self.indices = indices
        self.type_readers = {
                             "xml": read,
                             "traj": read,
                             "db": read,
                             "cif": read,
                             "xyz": read,
                             "dump": read_dump,
                             "OUTCAR": read,
                             "POSCAR": read,
                             "CONTCAR": read,
                             "vasp": read,
                             }
        self.set_types()
        self.set_reader()

    def set_types(self):
        self.types = {"output": self._check_type(self.output),
                      "inputs": [self._check_type(i) for i in self.inputs]}
        if len(np.unique(self.types["inputs"])) > 1:
            raise ValueError(
                 f"multiple input types detected:\t{self.types['inputs']}\n"
            )

    def set_reader(self):
        self.reader = self.type_readers[self.types["inputs"][0]]

    def _check_type(self, f):
        ftype = f.split(".")[-1]
        if ftype not in self.type_readers:
            types = self.type_readers.items()
            raise NotImplementedError(f"supported types:\t{types}\nharass me for others")
        return ftype

    def convert(self, **kwargs):
        traj = []
        for i in self.inputs:
            atoms = self.reader(i, index=self.indices, **kwargs)
            if len(traj) > 0 and len(atoms) > 1:
                # check to see if first image is identical to last image of previous file
                # primarily for concatenating MD runs from flex/overrun jobs
                pos1 = traj[-1].positions
                pos2 = atoms[0].positions
                if (pos1 == pos2).all():
                    atoms = atoms[1:]
            traj.extend(atoms)
        write(self.output, traj)

import numpy as np
from ase import Atoms
from ase.io import write, read
from ase.io.formats import string2index
from ase.data import chemical_symbols
import os
import json

from dptools.cli import BaseCLI

# TODO: figure out what to do about type_map
type_map = {"1": "O", "2": "Si", "3": "H"}
# type_map = {'1': 'C', '2': 'H', '3': 'H', '4': 'O', '5': 'O', '6': 'H', '7': 'Cu'}
def read_dump(dump, index=":"):
    with open(dump) as file:
        lines = file.readlines()
    traj = []
    # n_atoms = int(lines[3])
    for i, line in enumerate(lines):
        if "BOX BOUNDS" in line:
            n_atoms = int(lines[i - 1])
            lammps_cell = np.array([str_to_float(lines[i + j + 1]) for j in range(3)])
            cell, shift = convert_dump_cell(lammps_cell)
        elif "ITEM: ATOMS" in line:
            ids = [int(l.split()[0]) for l in lines[i + 1 : i + 1 + n_atoms]]
            sort = np.argsort(ids)
            # TODO: replace index hardcodinng
            types = np.array(
                [int(l.split()[-4]) for l in lines[i + 1 : i + 1 + n_atoms]]
            )
            symbols = np.array([type_map[str(t)] for t in types])
            positions = np.array(
                [str_to_float(lines[i + j + 1]) for j in range(n_atoms)]
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


def str_to_float(l):
    return list(map(float, l.split()[-3:]))


def convert_dump_cell(lammps_cell):
    """converts lammps dump cell format to ase"""
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
    with connect(db_name) as db:
        traj = [row.toatoms() for row in db.select()]
    return traj[string2index(indices)]

def graph2typemap(graph):
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
        raise TypeError(f"Unknown type_map format provided: {type_map_json}")
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

class Converter:
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
            raise NotImplementedError(f"supported types:\t{types}\nharass me for others")
        return ftype


    def convert(self):
        traj = []
        for i in self.inputs:
            atoms = self.reader(i, index=self.indices)
            if len(traj) > 0:
                # check to see if first image is identical to last image of previous file
                # primarily for concatenating MD runs from flex/overrun jobs
                pos1 = traj[-1].positions
                pos2 = atoms[0].positions
                if (pos1 == pos2).all():
                    print(len(atoms))
                    atoms = atoms[1:]
                    print(len(atoms))
            traj.extend(atoms)
        write(self.output, traj)

        
class CLI(BaseCLI):
    def add_args(self):
        self.parser.add_argument(
            "inputs",
            nargs="+",
            metavar="input",
            help="Input files (with extensions) to convert. Multiple inputs are concatenated into output",
        )
        self.parser.add_argument(
            "output",
            nargs=1,
            help="Output file name to write conversion to (with extension)",
        )
        self.parser.add_argument("-i", "--indices", nargs=1, type=str, default=":",
                help="Indices of input files to read. E.g., :10, -3:, :100:5")
        # self.parser.add_argument("-n", nargs=1, type=int,
        #        help="Max number of images to take from each db")
        # self.parser.add_argument("-p", "--path", nargs=1, type=str, default="./data",
        #        help="Specify path to dataset directory")

    def main(self, args):
        converter = Converter(args.inputs, args.output[0], args.indices)
        converter.convert()

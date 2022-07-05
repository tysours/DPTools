#!/usr/bin/env python
import numpy as np
from ase import Atoms
from ase.io import write

# TODO: figure out what to do about type_map
type_map = {'1': 'O', '2': 'Si', '3': 'H'}
#type_map = {'1': 'C', '2': 'H', '3': 'H', '4': 'O', '5': 'O', '6': 'H', '7': 'Cu'}
def read_dump(dump):
    with open(dump) as file:
        lines = file.readlines()
    traj = []
    #n_atoms = int(lines[3])
    for i, line in enumerate(lines):
        if "BOX BOUNDS" in line:
            n_atoms = int(lines[i-1])
            lammps_cell = np.array([str_to_float(lines[i+j+1]) for j in range(3)])
            cell, shift = convert_dump_cell(lammps_cell)
        elif "ITEM: ATOMS" in line:
            ids = [int(l.split()[0]) for l in lines[i+1:i+1+n_atoms]]
            sort = np.argsort(ids)
            # TODO: replace index hardcodinng
            types = np.array([int(l.split()[-4]) for l in lines[i+1:i+1+n_atoms]])
            symbols = np.array([type_map[str(t)] for t in types])
            positions = np.array([str_to_float(lines[i+j+1]) for j in range(n_atoms)])
            if 'xs' in line:
                positions = positions @ cell
            positions = positions - shift # shift atoms to origin for ASE Atoms object
            atoms = Atoms(positions=positions[sort], symbols=symbols[sort], cell=cell, pbc=True)
            atoms.set_tags(types[sort])
            traj.append(atoms)
    return traj

def str_to_float(l): 
    return list(map(float, l.split()[-3:]))

def convert_dump_cell(lammps_cell):
    '''converts lammps dump cell format to ase'''
    xlo_bound, xhi_bound = lammps_cell[0, :2]
    ylo_bound, yhi_bound = lammps_cell[1, :2]
    zlo_bound, zhi_bound = lammps_cell[2, :2]
    if lammps_cell.shape == (3, 3):
        xy, xz, yz = lammps_cell[:, -1]
    elif lammps_cell.shape == (3, 2):
        xy, xz, yz = 0.0, 0.0, 0.0

    xlo = xlo_bound - min((0.0, xy, xz, xy+xz))
    xhi = xhi_bound - max((0.0, xy, xz, xy+xz))
    ylo = ylo_bound - min((0.0, yz))
    yhi = yhi_bound - max((0.0, yz))
    zlo = zlo_bound
    zhi = zhi_bound

    a = [xhi - xlo, 0, 0]
    b = [xy, yhi-ylo, 0]
    c = [xz, yz, zhi-zlo]
    cell = np.array([a, b, c])
    shift = np.array([xlo, ylo, zlo])
    return cell, shift

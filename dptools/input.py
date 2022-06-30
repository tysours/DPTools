#!/usr/bin/env python
import numpy as np
from ase.db import connect
from ase.io.formats import string2index
import os
import sys
import shutil
import glob
from sklearn.utils import shuffle
import json
import requests

class DeepInput:
    def __init__(self, db_name, atoms=None, system_name=None, type_map=None, n=None):
        self.db_name = db_name
        if atoms is not None:
            self.atoms = atoms
        self.system_name = system_name
        self.n = n
        self.type_map = type_map
        self.set_dataset()
        self.write_input()

    def set_dataset(self):
        positions = []
        energies = []
        forces = []
        box = []
        n = self.n
        with connect(self.db_name) as db:
            for row in db.select():
                if not hasattr(self, 'atoms'):
                    self.atoms = row.toatoms() # saving for atom typing
                positions.append(row.positions.flatten())
                forces.append(row.forces.flatten())
                energies.append(row.energy)
                box.append(row.cell.flatten())

        positions = np.array(positions)
        forces = np.array(forces)
        energies = np.array(energies)
        box = np.array(box)
        positions, energies, forces, box = shuffle(positions, energies, forces, box)

        if n is not None and n < len(energies):
            positions = positions[:n]
            energies = energies[:n]
            forces = forces[:n]
            box = box[:n]

        self.positions = positions
        self.energies = energies
        self.forces = forces
        self.box = box

    def write_input(self):
        if self.system_name is None:
            system_name = self.db_name.split('/')[-1].split('.db')[0]
        else:
            system_name = self.system_name

        data_path = os.path.join("data", system_name)
        sets = ["train", "validation", "test"]
        self.paths = {s: os.path.join(data_path, s, "set.000") for s in sets}
        for s, path in self.paths.items():
            os.makedirs(path, exist_ok=True)

        n_train = int(np.ceil(len(self.energies) * 0.80)) # 80% train
        n_val = int(np.ceil(len(self.energies) * 0.90)) # 10% test, 10% val
        if n_val - n_train < 10: # need min of 10 for validation set
            n_train = n_val - 10
            if n_train < 1:
                raise ValueError(f"Need more images in {self.db_name}, \
                        {len(self.energies)} entries")
        
        self.write_types()
        self.write_npy("train", ":" + str(n_train))
        self.write_npy("validation", str(n_train) + ":" + str(n_val))
        self.write_npy("test", str(-n_val) + ":")

    def write_npy(self, dataset, indices):
        indices = string2index(indices)
        path = self.paths[dataset]
        np.save(os.path.join(path, "coord"), self.positions[indices])
        np.save(os.path.join(path, "force"), self.forces[indices])
        np.save(os.path.join(path, "energy"), self.energies[indices])
        np.save(os.path.join(path, "box"), self.box[indices])

    def write_types(self):
        symbols = self.atoms.get_chemical_symbols()
        if self.type_map is None:
            elements = np.unique(symbols)
            type_keys = {e: i for i, e in enumerate(elements)}
        else:
            type_keys = {v: k for k, v in self.type_map.items()}

        types = [type_keys[s] for s in symbols]

        type_paths = [os.path.join(path, "../type.raw") for s, path in self.paths.items()]
        for path in type_paths:
            np.savetxt(path, types, fmt="%.1i", newline=" ")

        self.type_map = {v: k for k, v in type_keys.items()}


class DeepInputs(DeepInput):
    def __init__(self, db_names, atoms=None, system_names=None, type_map=None, n=None):
        if atoms is None:
            atoms = [None] * len(db_names)
        elif not isinstance(atoms, list):
            atoms = [atoms]
        if system_names is None:
            system_names = [None] * len(db_names)
        elif isinstance(system_names, str):
            system_names = [system_names]
        if isinstance(db_names, str):
            db_names = [db_names]

        for db, a, sys in zip(db_names, atoms, system_names):
            dpi = DeepInput(db, a, sys, type_map, n)

        self.type_map = dpi.type_map

        self.get_json()
        self.update_json()
        self.write_json()

    def get_json(self):
        url = 'https://raw.githubusercontent.com/deepmodeling/deepmd-kit/master/examples/water/se_e3/input.json'
        r = requests.get(url, allow_redirects=True)
        self.input_json = json.loads(r.content)

    def update_json(self):
        # TODO: make this more customizable
        types = [self.type_map[i] for i in range(len(self.type_map))]
        systems = glob.glob('data/*') # don't put other files here
        systems.sort()

        self.input_json['model']['type_map'] = types
        self.input_json['model']['descriptor']['type'] = 'se_e2_a'
        self.input_json['model']['descriptor']['neuron'] = [16, 32, 64]
        self.input_json['model']['descriptor']['rcut'] = 6.0
        self.input_json['model']['descriptor']['rcut_smth'] = 5.5
        self.input_json['model']['descriptor']['axis_neuron'] = 16
        self.input_json['model']['fitting_net']['neuron'] = [64, 64, 64]
        self.input_json['training']['training_data']['systems'] = [f'{os.getcwd()}/{s}/train' for s in systems]
        self.input_json['training']['validation_data']['systems'] = [f'{os.getcwd()}/{s}/validation' for s in systems]
        self.input_json['training']['numb_steps'] = 1000000
        self.input_json['training']['disp_freq'] = 1000
        self.input_json['training']['save_freq'] = 100000

    def write_json(self):
        json_str = json.dumps(self.input_json, indent=4)
        with open('in.json', 'w') as file:
            file.write(json_str)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise Exception("Usage:\tdp_input.py [-n=size_of_training_set] system1.db [system2.db...]")

    n = None
    db_names = []
    for arg in sys.argv[1:]:
        if '-n' in arg:
            n = int(arg.split('=')[-1])
        elif '.db' in arg:
            db_names.append(arg)

    sys_names = []
    for db in db_names:
        dbn = db.split('/')[-1].split('.db')[0]
        sys_names.append(dbn)

    type_map = {0: 'C', 1: 'H', 2: 'N', 3: 'Zn'} # safer to set this manually
    thing = DeepInputs(db_names, system_names=sys_names, type_map=type_map, n=n)

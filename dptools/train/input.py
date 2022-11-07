"""
Module for writing deepmd training sets from ab-initio calculation results.
"""
import os
import glob
import json
import numpy as np
from ase.db import connect
from ase.io import read
from ase.data import atomic_numbers
from ase.io.formats import string2index
from sklearn.utils import shuffle


class DeepInput:
    """
    Class for writing training set compatible with deepmd-kit from ASE/VASP output
    (.traj, .db, vasprun.xml, etc.).

    Args:
        atoms_file (str): File containing training set configurations (e.g., .db).

        atoms (ase.Atoms or None): Optional Atoms object to use for assigning atom types.
            First image in atoms_file is used if None specified.

        system_name (str): Descriptive name of atomic system to use as directory name in
            dataset folder.

        type_map (dict or None): Dictionary mapping each atomic symbol to corresponding
            atom type index, optional and alphabetic order if used if None specified.
            E.g., {'Si': 0, 'O': 1}.

        n (int): Max number of images to take from atoms_file. All images are randomly
            shuffled and then n are taken for training.

        path (str): Path to dataset parent folder, makes folder if doesn't already exist.

        append (bool): If True, appends new configurations to current dataset if system_name
            dataset already exists.
    """

    def __init__(self, atoms_file, atoms=None, system_name=None, type_map=None, append=False, n=None, path="./data"):
        self.atoms_file = atoms_file
        if atoms is not None:
            self.atoms = atoms
        self.system_name = system_name
        self.n = n
        self.path = path
        self.type_map = type_map
        self._append = append
        self.set_dataset()
        self.write_input()

    def set_dataset(self):
        positions = []
        energies = []
        forces = []
        box = []
        n = self.n

        if self.atoms_file.endswith(".db"): # TODO: Rework this mess
            with connect(self.atoms_file) as db:
                for row in db.select():
                    if not hasattr(self, "atoms"):
                        self.atoms = row.toatoms() # saving for atom typing
                    self._check_indexing(list(row.numbers))
                    positions.append(row.positions.flatten())
                    forces.append(row.forces.flatten())
                    energies.append(row.energy)
                    box.append(row.cell.flatten())
        else:
            all_atoms = read(self.atoms_file, index=":")
            for atoms in all_atoms:
                if not hasattr(self, "atoms"):
                    self.atoms = atoms.copy() # saving for atom typing
                self._check_indexing(list(atoms.numbers))
                positions.append(atoms.positions.flatten())
                forces.append(atoms.get_forces().flatten())
                energies.append(atoms.get_potential_energy())
                box.append(atoms.cell.array.flatten())

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

    def _check_indexing(self, numbers):
        if not hasattr(self, "_ref"):
            self._ref = list(self.atoms.numbers)
            return
        if self._ref != numbers:
            if len(self._ref) != len(numbers):
                err = f"Multiple unique systems detected for {self.atoms_file}."
            else:
                err = f"Inconsistent indexing detected for {self.atoms_file}."
            symbol_map = {v: k for k, v in atomic_numbers.items()}
            ref_syms = [symbol_map[n] for n in self._ref]
            syms = [symbol_map[n] for n in numbers]
            err += f"\nConflicting system indices:\n\n{ref_syms}\n\n{syms}"
            raise Exception(err)

    def write_input(self):
        if self.system_name is None:
            system_name = self.atoms_file.split("/")[-1].split(".")[0]
        else:
            system_name = self.system_name
        data_path = os.path.join(self.path, system_name)
        sets = ["train", "validation", "test"]
        self.paths = {s: os.path.join(data_path, s, "set.000") for s in sets}
        for s, path in self.paths.items():
            os.makedirs(path, exist_ok=True)

        n_train = int(np.ceil(len(self.energies) * 0.80)) # 80% train
        n_val = int(np.ceil(len(self.energies) * 0.90)) # 10% test, 10% val
        if n_val - n_train < 10: # need min of 10 for validation set
            n_train = n_val - 10
            if n_train < 1:
                raise ValueError(f"Need more images in {self.atoms_file}, \
                        {len(self.energies)} entries")

        self.write_types()
        self.write_npy_set("train", ":" + str(n_train))
        self.write_npy_set("validation", str(n_train) + ":" + str(n_val))
        self.write_npy_set("test", str(n_val) + ":")

    def write_npy_set(self, dataset, indices):
        indices = string2index(indices)
        path = self.paths[dataset]
        self._write_npy_file(path, "coord", self.positions[indices])
        self._write_npy_file(path, "force", self.forces[indices])
        self._write_npy_file(path, "energy", self.energies[indices])
        self._write_npy_file(path, "box", self.box[indices])

    def _write_npy_file(self, path, key, vals):
        file_name = os.path.join(path, f"{key}.npy")
        if self._append and os.path.exists(file_name):
            old_vals = np.load(file_name)
            if old_vals.ndim == 2 and old_vals.shape[-1] != vals.shape[-1]:
                # check for matching system sizes if appending to old dataset
                raise ValueError(f"Tried appending to {file_name} but size mismatch found.")
            vals = np.append(old_vals, vals, axis=0)
        np.save(file_name, vals)

    def write_types(self):
        symbols = self.atoms.get_chemical_symbols()
        if self.type_map is None:
            elements = np.unique(symbols)
            type_keys = {e: i for i, e in enumerate(elements)}
        else:
            # inverting type_map, confusing and should probably be reworked
            type_keys = {v: k for k, v in self.type_map.items()}

        types = [type_keys[s] for s in symbols]

        type_paths = [os.path.join(path, "../type.raw") for s, path in self.paths.items()]
        for path in type_paths:
            np.savetxt(path, types, fmt="%.1i", newline=" ")

        self.type_map = {v: k for k, v in type_keys.items()}


class DeepInputs:
    """
    Class for writing training set compatible with deepmd-kit from multiple ASE/VASP outputs
    (.traj, .db, vasprun.xml, etc.).

    Args:
        db_names (str): File containing training set configurations (e.g., .db, .traj).
            TODO: update variable name to something more generic
        atoms (ase.Atoms or None): Optional Atoms object to use for assigning atom types.
            First image in atoms_file is used if None specified.
        system_names (list[str]): Descriptive name of atomic systems to use as directory names in
            dataset folder. Each name should be descriptive (e.g. '00_sodalite_10h2o') and unique
            for each db_names item, i.e., len(system_names) must equal len(db_names)
        type_map (dict or None): Dictionary mapping each atomic symbol to corresponding
            atom type index, optional and alphabetic order if used if None specified.
            E.g., {'Si': 0, 'O': 1}.
        n (int): Max number of images to take from atoms_file. All images are randomly
            shuffled and then n are taken for training.
        path (str): Path to dataset parent folder, makes folder if doesn't already exist.
    """

    def __init__(self,
                 db_names,
                 atoms=None,
                 system_names=None,
                 type_map=None,
                 append=False,
                 n=None,
                 in_json=None,
                 path="./data",
                 ):

        self.path = path
        os.makedirs(self.path, exist_ok=True)
        if atoms is None:
            atoms = self.get_atoms(db_names)
        elif not isinstance(atoms, list):
            atoms = [atoms]
        if system_names is None:
            system_names = [None] * len(db_names)
        elif isinstance(system_names, str):
            system_names = [system_names]
        if isinstance(db_names, str):
            db_names = [db_names]
        if type_map is None:
            type_map = self.get_type_map(atoms)
        if in_json is None:
            default_path = os.path.abspath(os.path.dirname(__file__))
            in_json = os.path.join(default_path, "in.json")

        self._check_names(db_names, system_names)

        self.type_map = type_map
        self._json_file = in_json

        for db, a, sys in zip(db_names, atoms, system_names):
            dpi = DeepInput(db, a, sys, self.type_map, append=append, n=n, path=path)

        self.set_json()
        self.update_json()
        self.write_json()

    def set_json(self):
        with open(self._json_file, "r") as file:
            self.input_json = json.loads(file.read())

    def update_json(self):
        self.set_systems()

        types = [self.type_map[i] for i in range(len(self.type_map))]
        self.input_json["model"]["type_map"] = types

    def set_systems(self):
        systems = [s for s in glob.glob(f"{self.path}/*") if os.path.isdir(s)]
        systems.sort()

        def get_paths(key):
            return [os.path.join(s, key) for s in systems]

        self.input_json["training"]["training_data"]["systems"] = get_paths("train")
        self.input_json["training"]["validation_data"]["systems"] = get_paths("validation")

    def write_json(self):
        json_str = json.dumps(self.input_json, indent=4)
        with open("in.json", "w") as file:
            file.write(json_str)

    @staticmethod
    def _check_names(input_files, system_names):
        n_in, n_sys, n_unique = len(input_files), len(system_names), len(np.unique(system_names))
        check1 = n_in != n_sys
        check2 = None not in system_names and n_unique != n_sys
        if check1 or check2:
            if check1:
                err = f"{n_sys} system_names provided for {n_in} input files"
            else:
                err = "Duplicate names detected in system_names, need all unique"
            raise ValueError(err)

    def get_atoms(self, db_names):
        atoms = []
        for dbn in db_names:
            if dbn.endswith(".db"):
                with connect(dbn) as db:
                    for row in db.select():
                        atoms.append(row.toatoms())
                        break
            else:
                atoms.append(read(dbn, index="0"))
        return atoms

    def get_type_map(self, atoms):
        """
        Check Atoms object from all systems for unique symbols, and then
        assigns type_map in alphabetical order.

        Args:
            atoms (list[ase.Atoms]): List of example Atoms object from all systems
                that will be used for training (e.g. the first image from all vasprun inputs).

        Returns:
            type_map (dict): Dictionary mapping each atom type index to atomic symbol in
                alphabetical order.
        """
        tm_path = os.path.join(self.path, "type_map.json")
        if "type_map.json" in os.listdir(self.path):
            print(f"READING {tm_path}")
            with open(tm_path, "r") as file:
                type_map = json.loads(file.read())
            type_map = {int(i): s for i, s in type_map.items()}
        else:
            symbols = []
            for a in atoms:
                symbols.extend(np.unique(a.get_chemical_symbols()))

            symbols = np.unique(symbols)
            type_map = dict(enumerate(symbols))
            print(f"WRITING TYPE MAP TO {tm_path}")
            with open(tm_path, "w") as file:
                file.write(json.dumps(type_map, indent=2))

        print("TYPES:")
        for i, t in type_map.items():
            print(f"\t{i}\t{t}")
        print("If unhappy with above type ordering, edit type_map.json to your liking and rerun!")

        return type_map

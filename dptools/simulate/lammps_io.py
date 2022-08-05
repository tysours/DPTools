#import lammps
import numpy as np
import os
import sys
import json
from ase.neighborlist import NeighborList
from ase.neighborlist import natural_cutoffs
from ase.data import atomic_masses, atomic_numbers
from ase.geometry.analysis import Analysis
from textwrap import dedent
from ase.calculators.lammpslib import convert_cell

#with open(f'uff4mof.json', 'r') as file:
#    lj_types = json.load(file)

class LammpsInput:
    """
    Creates lammps input files from ASE Atoms object
    Messy and needs to be redone

    Parameters
    ----------
    atoms: ASE Atoms object, structure used for lammps calculation
    types: dict, map atom type index to element symbol
        e.g., {1: 'O', 2: 'Si'}
    charges: list, list of charges (float) on each atom 
    write_bonds: bool, define all bonds of structure in structure data file
    name: str, name used for creating input files
    atom_style: str, lammps style for atomic positions, groups, etc
    pair_style: str, lammps pair potential style command
    bond_style: str, lammps bond style command
    angle_style: str, lammps angle style command
    kspace_style: str, lammps kspace style command
    groups: list, list of groups for each atom
    coeffs: dict, maps FF params to atom types, #TODO: rework this
    pair_coeffs: list[str], pair_coeff lines to define ij interactions
    cutoff: float, cutoff radius for relevant pair potentials
    """
        
    def __init__(self, atoms, types, charges=None, 
                 write_bonds=False,
                 name='atoms',
                 atom_style='full',
                 pair_style='lj/cut/coul/long',
                 bond_style=None,
                 angle_style=None,
                 kspace_style=None,
                 groups=None,
                 coeffs=None,
                 pair_coeffs=None,
                 cutoff=9.0, 
                 sf=None):

        if charges is None:
            charges = atoms.get_initial_charges()

        if groups is None:
            groups = np.zeros(len(atoms), dtype=int)

        if sf is None:
            sf = [1, 1]

        self.atoms = atoms

        # key parameters and system info for writing lammps input + data file
        self.info = {"data": {},
                     "input": {}}

        self.types = types
        self.coeffs = coeffs
        self.pair_coeffs = pair_coeffs
        self.charges = charges
        self.groups = groups
        self.info["data"]["natoms"] = len(atoms)
        self.info["data"]["ntypes"] = len(types)
        self.info["data"]["cell"] = self.atoms.cell
        self.info["data"]["atom_style"] = atom_style
        #self.atom_style = atom_style
        #self.pair_style = pair_style
        #self.angle_style = angle_style
        #self.bond_style = bond_style
        #self.kspace_style = kspace_style
        self.info["input"]["atom_style"] = atom_style
        self.info["input"]["pair_style"] = pair_style
        self.info["input"]["angle_style"] = angle_style
        self.info["input"]["bond_style"] = bond_style
        self.info["input"]["kspace_style"] = kspace_style
        self.write_bonds = write_bonds
        self.cutoff = cutoff
        self.sf = sf
        self.symbols = np.array(atoms.get_chemical_symbols())
        self.name = name

    def set_atoms(self, atoms):
        self.atoms = atoms

    def write_atoms(self, atoms=None, charges=None):
        if atoms is not None:
            self.set_atoms(atoms)
        if charges is not None:
            self.charges = charges
        self._write_atoms(self.write_bonds, self.info["data"]["atom_style"])

    def write_input(self):
        self.input = self._get_input(self.info["input"]["atom_style"],
                                     self.info["input"]["pair_style"], 
                                     self.info["input"]["bond_style"], 
                                     self.info["input"]["angle_style"], 
                                     self.info["input"]["kspace_style"], 
                                     self.groups, 
                                     self.cutoff)


    def _write_atoms(self, write_bonds=False, atom_style='full'):
        #n_atoms = len(self.atoms)
        n_types = len(self.types.keys())

        types_str = ""
        coeffs_str = ""
        if self.coeffs is not None:
            coeffs_str += "Pair Coeffs\n\n"
        for k, v in self.types.items():
            sym = v.split('_')[0]
            mass = atomic_masses[atomic_numbers[sym]]
            types_str += f"{k} {mass} # {v}\n"
            if self.coeffs is not None:
                eps = self.coeffs[k]['eps'] * self.sf[0] 
                sig = self.coeffs[k]['sig'] * self.sf[1]
                coeffs_str += f"{k} {eps} {sig}\n"

        #### POSITIONS ####
        coords_str = ""

        for a, g, q, (x, y, z) in zip(self.atoms, 
                                      self.groups,
                                      self.charges, 
                                      self.atoms.positions):

            #coords_str += f" {a.index+id_start} {g} {a.tag} {q} {x:.5f} {y:.5f} {z:.5f}\n"
            if atom_style == 'full':
                coords_str += f" {a.index + 1} {g} {a.tag} {q} {x} {y} {z}\n"
            else:
                coords_str += f" {a.index + 1} {a.tag} {x} {y} {z}\n"


        #### BONDS ####
        if write_bonds:
            bonds_str = self.get_bonds()
            #n_bonds = self.n_bonds
            #n_b_types = self.n_b_types
        else:
            bonds_str = ""
            #n_bonds = 0
            #n_b_types = 0
            self.info["data"]["nbonds"] = 0
            self.info["data"]["nbtypes"] = 0

        self.info["data"]["types"] = types_str
        self.info["data"]["coords"] = coords_str
        self.info["data"]["coeffs"] = coeffs_str
        self.info["data"]["bonds"] = bonds_str

        temp = DataTemplate(self.name)
        for key, val in self.info["data"].items():
            temp.set(key, val)
        #temp.natoms = n_atoms
        #temp.set("natoms", n_atoms)
        #temp.nbonds = n_bonds
        #temp.ntypes = n_types
        #temp.nbtypes = n_b_types
        #temp.cell = self.atoms.cell
        #temp.types = types_str
        #temp.atom_style = atom_style
        #temp.coeffs = coeffs_str
        #temp.coords = coords_str
        #temp.bonds = bonds_str

        temp.write(f"data.{self.name}", temp.data)

        return 

            
    def _get_input(self, 
                   atom_style, 
                   pair_style, 
                   bond_style, 
                   angle_style, 
                   kspace_style, 
                   groups, 
                   cutoff):

        if cutoff is None:
            cutoff = ''

        temp = InputTemplate(self.name)
        #temp.atom_style = atom_style 
        temp.set("atom_style", atom_style)
        #temp.pair_style = pair_style
        temp.set("pair_style", pair_style)
        #temp.bond_style = bond_style
        temp.set("angle_style", angle_style)
        temp.set("bond_style", bond_style)

        # XXX: maybe makes more sense to move this to InputTemplate
        #      as set_pair_coeffs method etc.
        if self.coeffs is None and self.pair_coeffs is None:
            temp.data += "pair_coeff * *\n"
        if self.pair_coeffs is not None:
            if isinstance(self.pair_coeffs, str):
                temp.data += self.pair_coeffs
            elif isinstance(self.pair_coeffs, list):
                for line in self.pair_coeffs:
                    temp.data += line
            else:
                raise TypeError("str or list needed for pair_coeffs")
        if kspace_style is not None:
            temp.data += f"kspace_style\t{kspace_style}\n\n"

        # XXX: groups is never None? rework groups eventually
        if groups is not None:
            #print("REMINDER TO REMOVE GROUP HARDCODING")
            temp.data += "group\tsilica molecule 0\n"
#            for n, group in groups.items():
#                temp.data += f"group\t{group} molecule {n}\n"
        temp.write(f"in.{self.name}", temp.data)
        return temp.data

    def get_coords(self):
        pass

    def get_bonds(self):
        anal = Analysis(self.atoms)
        bond_types = {}

        def b_str(t1, t2): return f"{t1}-{t2}" if t1 < t2 else f"{t2}-{t1}"
        for i, bonds in enumerate(anal.unique_bonds[0]):
            for bond in bonds:
                b_type = b_str(self.tags[i], self.tags[bond])
                if b_type in bond_types:
                    bond_types[b_type].append((i, bond))
                else:
                    bond_types[b_type] = [(i, bond)]
            
        #self.n_b_types = len(bond_types.keys())

        bonds_str = "Bonds\n\n"
        n_bond = 0
        for i, (b_type, bonds) in enumerate(bond_types.items()):
            for bond in bonds:
                bonds_str += f"\t{n_bond+1}\t{i+k}\t{bond[0]+1}\t{bond[1]+1}\n"
                n_bond += 1

        #self.n_bonds = n_bond
        self.info["data"]["nbonds"] = n_bond
        self.info["data"]["nbtypes"] = len(bond_types.keys())
        return bonds_str

class Template:
    def write(self, name, text):
        with open(name, 'w') as file:
            file.write(text)
    
    def set(self, name, value):
        try:
            getattr(self, f"set_{name}")(value)
        except AttributeError:
            self.data = self.data.replace(f"<{name}>", str(value))


class DataTemplate(Template):
    def __init__(self, name):
        self.name = name
        self.data = dedent('''\
        LAMMPS data file

          <natoms> atoms
          <nbonds> bonds
          <ntypes> atom types
          <nbtypes> bond types
          0 angle types

          <x> xlo xhi
          <y> ylo yhi
          <z> zlo zhi
          <xyxzyz> xy xz yz

        Masses

        <types>

        <coeffs>

        Atoms # <atom_style>

        <coords>

        <bonds>
        ''')

    @property
    def natoms(self):
        return

    @natoms.setter
    def natoms(self, value):
        self.data = self.data.replace("<natoms>", str(value))

    @property
    def nbonds(self):
        return

    @natoms.setter
    def nbonds(self, value):
        self.data = self.data.replace("<nbonds>", str(value))

    @property
    def ntypes(self):
        return

    @ntypes.setter
    def ntypes(self, value):
        self.data = self.data.replace("<ntypes>", str(value))

    @property
    def nbtypes(self):
        return

    @nbtypes.setter
    def nbtypes(self, value):
        self.data = self.data.replace("<nbtypes>", str(value))

    @property
    def cell(self):
        return

    def set_cell(self, atoms_cell):
        cell = convert_cell(atoms_cell)[0]
        x = f"0 {cell[0, 0]}"
        y = f"0 {cell[1, 1]}"
        z = f"0 {cell[2, 2]}"
        xy, xz, yz = cell[0, 1], cell[0, 2], cell[1, 2]
        xyxzyz = f"{xy} {xz} {yz}"

        self.data = self.data.replace("<x>", x)
        self.data = self.data.replace("<y>", y)
        self.data = self.data.replace("<z>", z)
        self.data = self.data.replace("<xyxzyz>", xyxzyz)

    @cell.setter
    def cell(self, atoms_cell):

        cell = convert_cell(atoms_cell)[0]
        x = f"0 {cell[0, 0]}"
        y = f"0 {cell[1, 1]}"
        z = f"0 {cell[2, 2]}"
        xy, xz, yz = cell[0, 1], cell[0, 2], cell[1, 2]
        xyxzyz = f"{xy} {xz} {yz}"

        self.data = self.data.replace("<x>", x)
        self.data = self.data.replace("<y>", y)
        self.data = self.data.replace("<z>", z)
        self.data = self.data.replace("<xyxzyz>", xyxzyz)

    @property
    def types(self):
        return

    @types.setter
    def types(self, value):
        self.data = self.data.replace("<types>", str(value))

    @property
    def atom_style(self):
        return

    @atom_style.setter
    def atom_style(self, value):
        self.data = self.data.replace("<atom_style>", str(value))

    @property
    def coeffs(self):
        return

    @coeffs.setter
    def coeffs(self, value):
        self.data = self.data.replace("<coeffs>", str(value))

    @property
    def coords(self):
        return

    @coords.setter
    def coords(self, value):
        self.data = self.data.replace("<coords>", str(value))

    @property
    def bonds(self):
        return

    @coords.setter
    def bonds(self, value):
        self.data = self.data.replace("<bonds>", str(value))

class InputTemplate(Template):
    def __init__(self, name):
        self.name = name
        self.data = dedent(f'''\
        units\t\tmetal
        boundary\tp p p
        atom_style\t<atom_style>
        atom_modify\tmap array

        pair_style\t<pair_style>
        <bond_style>
        <angle_style>

        box tilt\tlarge
        read_data\tdata.{name}
        thermo_style custom step temp etotal pe press pxx pyy pzz pxy pxz pyz lx ly lz vol
        ''')

    @property
    def atom_style(self):
        return

    @atom_style.setter
    def atom_style(self, value):
        self.data = self.data.replace("<atom_style>", str(value))

    @property
    def pair_style(self):
        return

    @pair_style.setter
    def pair_style(self, value):
        self.data = self.data.replace("<pair_style>", str(value))

    @property
    def bond_style(self):
        return

    @bond_style.setter
    def bond_style(self, value):
        if value is None:
            self.data = self.data.replace("<bond_style>", "")
        else:
            self.data = self.data.replace("<bond_style>",
                                          f"bond_style\t{value}")

    def set_bond_style(self, value):
        if value is None:
            self.data = self.data.replace("<bond_style>", "")
        else:
            self.data = self.data.replace("<bond_style>",
                                          f"bond_style\t{value}")

    @property
    def angle_style(self):
        return

    @angle_style.setter
    def angle_style(self, value):
        if value is None:
            self.data = self.data.replace("<angle_style>", "")
        else:
            self.data = self.data.replace("<angle_style>",
                                          f"angle_style\t{value}")

    def set_angle_style(self, value):
        if value is None:
            self.data = self.data.replace("<angle_style>", "")
        else:
            self.data = self.data.replace("<angle_style>",
                                          f"angle_style\t{value}")

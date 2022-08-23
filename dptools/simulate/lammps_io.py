#import lammps
import numpy as np
import os
import sys
import json
import re
from ase.neighborlist import NeighborList
from ase.neighborlist import natural_cutoffs
from ase.data import atomic_masses, atomic_numbers
from ase.geometry.analysis import Analysis
from textwrap import dedent
from ase.calculators.lammpslib import convert_cell


class LammpsInput:
    """
    Creates lammps input files from ASE Atoms object
    Messy and needs to be redone

    Parameters
    ----------
    atoms: ASE Atoms object, structure used for lammps calculation

    type_dict: dict, map atom type index to element symbol 
               (Element_tag to specify multiple types of same element)
               e.g., {1: 'O', 2: 'Si', 3: 'O_h2o', 4: 'H_h2o'}

    charges: list, list of charges (float) on each atom 

    bonds: bool, define all bonds in structure data file
    angles: bool, define all angles in structure data file
    dihedrals: bool, define all dihedral angles in structure data file
    impropers: bool, define impropers in structure data file

    name: str, name used for creating input files

    atom_style: str, lammps style for atomic positions, groups, etc
    pair_style: str, lammps pair potential style command
    bond_style: str, lammps bond style command
    angle_style: str, lammps angle style command
    kspace_style: str, lammps kspace style command

    groups: list, list of groups for each atom

    coeffs_dict: dict, maps FF params to atom types, #TODO: rework this
    pair_coeffs: list[str], pair_coeff line(s) to define ij interactions
    """
        
    def __init__(self, atoms, type_dict, 
                 charges=None, 
                 bonds=False,
                 angles=False,
                 dihedrals=False,
                 impropers=False,
                 name="atoms",
                 atom_style="full",
                 pair_style=None,
                 bond_style=None,
                 angle_style=None,
                 kspace_style=None,
                 groups=None,
                 coeffs_dict=None,
                 pair_coeffs=None,
                 ):

        self.atoms = atoms
        self.set_style("atom", atom_style)
        self.set_style("pair", pair_style)
        self.set_style("bond", bond_style)
        self.set_style("angle", angle_style)
        self.set_style("kspace", kspace_style)

        if charges is None:
            charges = atoms.get_initial_charges()
        self.charges = charges
        self.groups = groups
        self.type_dict = type_dict
        self.coeffs_dict = coeffs_dict
        self.pair_coeffs = pair_coeffs
        self._bonds = bonds
        self._angles = angles
        self._dihedrals = dihedrals
        self._impropers = impropers
        self.name = name

    def set_style(self, style, text):
        style = style if style.endswith("_style") else f"{style}_style"
        if text and not text.startswith(style):
            text = f"{style} {text}"
        setattr(self, style, text or "")

    def write(self, atoms=None, charges=None):
        self.write_atoms(atoms=atoms, charges=charges)
        self.write_infile()

    def write_atoms(self, atoms=None, charges=None):
        atoms = atoms if atoms is not None else self.atoms
        charges = charges if charges is not None else self.charges
        self.natoms = len(atoms)
        self.write_cell()
        self.write_types()
        self.write_coords()

        for key in ["bonds", "angles", "dihedrals", "impropers"]:
            self.write_geometry(key)

        datatemp = DataTemplate(f"data.{self.name}", self)
        datatemp.write()

    def write_geometry(self, key):
        if getattr(self, f"_{key}"): # e.g.  if self._bonds:
            writer = getattr(self, f"write_{key}") # self.write_bonds()
            writer()
        else:
            setattr(self, key, "")
            setattr(self, f"n{key}", 0)
            setattr(self, f"n{key[0]}types", 0)

    def write_cell(self):
        cell = convert_cell(self.atoms.cell)[0]
        self.x = f"0 {cell[0, 0]}"
        self.y = f"0 {cell[1, 1]}"
        self.z = f"0 {cell[2, 2]}"
        xy, xz, yz = cell[0, 1], cell[0, 2], cell[1, 2]
        self.xyxzyz = f"{xy} {xz} {yz}"

    def write_types(self):
        self.ntypes = len(self.type_dict.keys())

        types_str = ""
        coeffs_str = ""
        if self.coeffs_dict is not None:
            coeffs_str += "Pair Coeffs\n\n"

        for k, v in self.type_dict.items():
            sym = v.split('_')[0]
            mass = atomic_masses[atomic_numbers[sym]]
            types_str += f"{k} {mass} # {v}\n"
            if self.coeffs_dict is not None:
                coeffs = ' '.join(self.coeffs_dict[k])
                coeffs_str += f"{k} {coeffs}\n"

        self.types = types_str
        self.coeffs = coeffs_str

    def write_coords(self):
        coords_str = ""
        zeros = np.zeros(self.natoms, dtype=int)
        groups = self.groups if self.groups is not None else zeros
        for a, g, q, (x, y, z) in zip(self.atoms, 
                                      groups,
                                      self.charges, 
                                      self.atoms.positions):

            if not self.atom_style or self.atom_style == "atom_style full":
                coords_str += f" {a.index + 1} {g} {a.tag} {q} {x} {y} {z}\n"
            else:
                err = f"atom_style {self.atom_style} not supported, harass me for it"
                raise NotImplementedError(err)
                coords_str += f" {a.index + 1} {a.tag} {x} {y} {z}\n"

        self.coords = coords_str
        return

    def write_bonds(self):
        anal = Analysis(self.atoms) # pronounced uh-nahl
        bond_types = {}

        def b_str(t1, t2): 
            return f"{t1}-{t2}" if t1 < t2 else f"{t2}-{t1}"

        for i, bonds in enumerate(anal.unique_bonds[0]):
            for bond in bonds:
                b_type = b_str(self.tags[i], self.tags[bond])
                if b_type in bond_types:
                    bond_types[b_type].append((i, bond))
                else:
                    bond_types[b_type] = [(i, bond)]
            
        bonds_str = "Bonds\n\n"
        n_bond = 0
        for i, (b_type, bonds) in enumerate(bond_types.items()):
            for bond in bonds: # I can't remember what k is here, 
                               # I'm assuming this code fails but haven't checked
                bonds_str += f"\t{n_bond+1}\t{i+k}\t{bond[0]+1}\t{bond[1]+1}\n"
                n_bond += 1

        self.nbonds = n_bond
        self.nbtypes = len(bond_types.keys())
        self.bonds = bond_str

    def write_angles(self):
        raise NotImplementedError("Too lazy to add angles, harass me if you need it")

    def write_dihedrals(self):
        raise NotImplementedError("Too lazy to add dihedrals, harass me if you need it")
            
    def write_impropers(self):
        raise NotImplementedError("I don't even know what this means,"\
                " but i'll figure it out if you need it")

    def write_infile(self): 
        if not self.coeffs_dict and not self.pair_coeffs:
            self.pair_coeffs = "pair_coeff * *\n"
        elif self.pair_coeffs is not None:
            if isinstance(self.pair_coeffs, list):
                self.pair_coeffs = '\n'.join(self.pair_coeffs)
            elif not isinstance(self.pair_coeffs, str):
                raise TypeError("str or list needed for pair_coeffs")

        if self.groups is not None:
            raise NotImplementedError("Harass me if you need it")

        intemp = InputTemplate(f"in.{self.name}", self)
        intemp.write()


class Template:
    def __init__(self, file_name, lammps_input):
        self.file_name = file_name
        self.input = lammps_input

    def write(self):
        self.fill()
        self.trim()
        with open(self.file_name, 'w') as file:
            file.write(self.text)

    def fill(self):
        pattern = "<\w+>"
        matches = re.findall(pattern, self.text)
        for match in matches:
            key = match[1:-1]
            attr = getattr(self.input, key)
            attr = str(attr) if attr is not None else ""
            self.text = self.text.replace(match, attr)

    def trim(self):
        while "\n\n\n" in self.text:
            self.text = self.text.replace("\n\n\n", "\n\n")


# XXX: Don't really have a need for subclasses anymore, but it works
class DataTemplate(Template):
    text = dedent('''\
        LAMMPS data file

          <natoms> atoms
          <nbonds> bonds
          <nangles> angles
          <ndihedrals> dihedrals
          <nimpropers> impropers

          <ntypes> atom types
          <nbtypes> bond types
          <natypes> angle types
          <ndtypes> dihedral types
          <nitypes> improper types

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

        <dihedrals>

        <impropers>
        ''')


class InputTemplate(Template):
    text = dedent('''\
        units\t\tmetal
        boundary\tp p p
        <atom_style>
        atom_modify\tmap array

        <pair_style>
        <bond_style>
        <angle_style>
        <kspace_style>

        box tilt\tlarge
        read_data\tdata.<name>
        <pair_coeffs>
        <groups>
        thermo_style custom step temp etotal pe press pxx pyy pzz pxy pxz pyz lx ly lz vol
        ''')

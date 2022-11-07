import re
from textwrap import dedent
import numpy as np
from ase.data import atomic_masses, atomic_numbers
from ase.geometry.analysis import Analysis
from ase.calculators.lammpslib import convert_cell


class LammpsInput:
    """
    Creates lammps input files from ASE Atoms object. Works by setting as str attributes
    all neccessary lammps input information and commands, which are then inserted into
    the appropriate Template subclass.


    Args:
        atoms (ase.Atoms): structure used for lammps calculation

        type_dict (dict): map atom type index to element symbol
                   (Element_tag to specify multiple types of same element)
                   e.g., {1: 'O', 2: 'Si', 3: 'O_h2o', 4: 'H_h2o'}

        charges (array-like): List or array of charges (float) on each atom.
            Must have len(charges) == len(atoms).

        bonds (bool): Define all bonds in structure data file if True.
        angles (bool): Define all angles in structure data file if True.
        dihedrals (bool): Define all dihedral angles in structure data file if True.
        impropers (bool): Define impropers in structure data file if True.

        name (str, optional): Name used for creating input files (name.data, in.name).

        atom_style (str, optional): lammps style for atomic positions, groups, etc.
        pair_style (str, optional): lammps pair_style command.
        bond_style (str, optional): lammps bond_style command.
        angle_style (str, optional): lammps angle_style command.
        kspace_style (str, optional): lammps kspace_style command.

        groups (array-like, optional): List of groups (int) for each atom.
            Must have len(groups) == len(atoms).

        pair_coeff (list[str] or str, optional): lammps pair_coeff line(s) to define ij interactions
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
                 pair_coeff=None,
                 bond_coeff=None,
                 angle_coeff=None,
                 groups=None,
                 ):

        self.atoms = atoms
        self.set_lmp_cmd("atom_style", atom_style)
        self.set_lmp_cmd("pair_style", pair_style)
        self.set_lmp_cmd("bond_style", bond_style)
        self.set_lmp_cmd("angle_style", angle_style)
        self.set_lmp_cmd("kspace_style", kspace_style)
        self.set_lmp_cmd("pair_coeff", pair_coeff)
        self.set_lmp_cmd("bond_coeff", bond_coeff)
        self.set_lmp_cmd("angle_coeff", angle_coeff)
        self.atom_style_hint = self.atom_style.split()[-1]

        if charges is None:
            charges = atoms.get_initial_charges()
        self.charges = charges
        self.groups = groups
        self.type_dict = type_dict
        self._bonds = bonds
        self._angles = angles
        self._dihedrals = dihedrals
        self._impropers = impropers
        self.name = name

    def set_lmp_cmd(self, command, text):
        """
        Set lammps commands that follow the pattern: command args

        Args:
            command (str): Name of lammps command, e.g., pair_style.
            text (list[str] or str): Arguments to use with command. If text doesn't
                lead with command, then command is prepended to text.
        """
        if isinstance(text, list):
            lines = [self.prepend_command(command, l) for l in text]
            new_text = "\n".join(lines)
        else:
            new_text = self.prepend_command(command, text)
        setattr(self, command, new_text or "")

    @staticmethod
    def prepend_command(command, text):
        """
        Prepend command to corresponding arguments str.

        Args:
            command (str): Name of lammps command to prepend to text.
            text (str): lammps arg str corresponding to command.

        Returns:
            str: Full lammps line with command prepended to text.

        Examples:
            self.prepend_command('kspace_style', 'pppm 1e-5')
            'kspace_style pppm 1e-5'
        """
        if text and not text.startswith(command):
            text = f"{command} {text}"
        return text

    def write(self, atoms=None, charges=None):
        """
        Writes lammps data file and input file for atoms.

        Args:
            atoms (ase.Atoms or None): New atoms object used to write data file
                (or self.atoms if atoms is None).
            charges (array-like or None): Optional charges corresponding to atoms.
        """
        self.write_atoms(atoms=atoms, charges=charges)
        self.write_infile()

    def write_atoms(self, atoms=None, charges=None):
        """
        Write lammps data file from atoms. Writes unit cell info, atom types,
        atomic positions, and bonds, angles, dihedrals, impropers if specified in __init__().

        Args:
            atoms (ase.Atoms or None): New atoms object used to write data file
                (or self.atoms if atoms is None).
            charges (array-like or None): Optional charges corresponding to atoms.
        """
        atoms = atoms if atoms is not None else self.atoms
        charges = charges if charges is not None else self.charges
        self.natoms = len(atoms)
        self.write_cell()
        self.write_types()
        self.write_coords()
        self.write_constraints(atoms)

        for key in ["bonds", "angles", "dihedrals", "impropers"]:
            self.write_geometry(key)

        datatemp = DataTemplate(f"data.{self.name}", self)
        datatemp.write()

    def write_cell(self):
        """Transform and write self.atoms' ``ase.cell.Cell`` to lammps data file."""
        cell = convert_cell(self.atoms.cell)[0]
        self.x = f"0 {cell[0, 0]}"
        self.y = f"0 {cell[1, 1]}"
        self.z = f"0 {cell[2, 2]}"
        xy, xz, yz = cell[0, 1], cell[0, 2], cell[1, 2]
        self.xyxzyz = f"{xy} {xz} {yz}"

    def write_types(self):
        """Write Types section in lammps data file (atomic masses for each atom type)."""
        self.ntypes = len(self.type_dict.keys())

        types_str = ""
        for k, v in self.type_dict.items():
            sym = v.split("_")[0]
            mass = atomic_masses[atomic_numbers[sym]]
            types_str += f"{k} {mass} # {v}\n"

        self.types = types_str

    def write_coords(self):
        """Write Coords section (atomic positions) in lammps datafile."""
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
                err = f"atom_style {self.atom_style} not supported, harass me for it, "\
                    "but I can't imagine why you'd need it for deepmd."
                raise NotImplementedError(err)
                #coords_str += f" {a.index + 1} {a.tag} {x} {y} {z}\n"

        self.coords = coords_str

    def write_constraints(self, atoms):
        if not atoms.constraints:
            self.constraints = ""
            return
        indices = atoms.constraints[0].get_indices().copy()
        indices += np.ones(len(indices), dtype="int64")
        constrained = " ".join(list(map(str, indices)))
        self.constraints = f"group constrained id {constrained}"
        self.constraints += "\ngroup unconstrained subtract all constrained"
        self.constraints += "\n\nfix constraints constrained setforce 0.0 0.0 0.0"

    def write_geometry(self, key):
        """
        Generalized method to write bonds, angles, maybe dihedrals (untested) to lammps data file.
        Uses ``ase.geometry.Analysis`` to generate list of bonds, angles, etc.

        Args:
            key (str): Geometry component to write ('bonds', 'angles', 'dihedrals', 'impropers').
        """
        n = 0
        n_types = 0
        text = ""
        if getattr(self, f"_{key}"): # e.g. if _bonds, write bonds
            if key in ["dihedrals", "impropers"]:
                raise NotImplementedError(f"{key} not implemented, harass me if you need it")

            # define order of indices when writing key
            # (e.g. angles need central atom in middle, 1-0-2)
            orders = {"bonds": "01", "angles": "102", "dihedrals": "0123"}
            if not hasattr(self, "anal"): # only calc once
                self.anal = Analysis(self.atoms)

            def t_str(order, *t):
                tsorted = [str(sorted(t)[int(i)]) for i in order]
                return "-".join(tsorted)

            tags = self.atoms.get_tags()
            types = {}
            unique = getattr(self.anal, f"unique_{key}")[0]
            for i, groups in enumerate(unique):
                for neighbors in groups:
                    if isinstance(neighbors, np.int32):
                        neighbors = [neighbors] # bonds only have single (int) neighbor
                    typ = t_str(orders[key], tags[i], *[tags[n] for n in neighbors])

                    if typ in types:
                        types[typ].append((i, *neighbors))
                    else:
                        types[typ] = [(i, *neighbors)]

            n_types = len(types)
            text = key.capitalize() + "\n\n"
            #for i, (typ, groups) in enumerate(types.items()):
            for i, typ in enumerate(sorted(types.keys())):
                for group in types[typ]:
                    g_str = "\t".join([str(g + 1) for g in group])
                    text += f" {n+1}\t{i+1}\t{g_str}\n"
                    n += 1

        setattr(self, key, text)
        setattr(self, f"n{key}", n)
        setattr(self, f"n{key[0]}types", n_types)

    def write_infile(self):
        """
        Write lammps input file containing all general setup commands
        (e.g. define units, read data file, etc.).
        """
        if not self.pair_coeff:
            self.pair_coeff = "pair_coeff * *\n"

        if self.groups is not None:
            raise NotImplementedError("Harass me if you need it")

        intemp = InputTemplate(f"in.{self.name}", self)
        intemp.write()

    def _write_geometry(self, key):
        """
        Deprecated, use new write_geometry. Generalized method to write geometry components
        (bonds, angles, dihedrals, or impropers) to lammps data file and set quantities
        (num bonds, bond types, etc.).

        Args:
            key (str): geometry component to write
                ('bonds', 'angles', 'dihderals', or 'impropers').
        """
        if getattr(self, f"_{key}"): # e.g.  if self._bonds:
            writer = getattr(self, f"write_{key}") # self.write_bonds()
            writer()
        else:
            setattr(self, key, "")
            setattr(self, f"n{key}", 0)
            setattr(self, f"n{key[0]}types", 0)

    def write_bonds(self):
        """
        (Deprecated, may restore) Write all bonds in self.atoms to lammps datafile.
        """
        self.anal = Analysis(self.atoms)
        tags = self.atoms.get_tags()
        bond_types = {}

        def b_str(t1, t2):
            return f"{t1}-{t2}" if t1 < t2 else f"{t2}-{t1}"

        for i, bonds in enumerate(self.anal.unique_bonds[0]):
            for bond in bonds:
                b_type = b_str(tags[i], tags[bond])
                if b_type in bond_types:
                    bond_types[b_type].append((i, bond))
                else:
                    bond_types[b_type] = [(i, bond)]

        bonds_str = "Bonds\n\n"
        n_bond = 0
        for i, (b_type, bonds) in enumerate(bond_types.items()):
            for bond in bonds:
                bonds_str += f"\t{n_bond+1}\t{i+1}\t{bond[0]+1}\t{bond[1]+1}\n"
                n_bond += 1

        self.nbonds = n_bond
        self.nbtypes = len(bond_types.keys())
        self.bonds = bonds_str

    def write_angles(self):
        """
        (Deprecated, may restore) Write all angles in self.atoms to lammps datafile.
        """
        if not hasattr(self, "anal"): # don't recalc if already done in write_bonds()
            self.anal = Analysis(self.atoms)
        tags = self.atoms.get_tags()
        angle_types = {}

        def a_str(t1, t2, t3):
            t = sorted([t1, t2, t3])
            return f"{t[1]}-{t[0]}-{t[2]}"

        for i, angles in enumerate(self.anal.unique_angles[0]):
            for angle in angles:
                a_type = a_str(tags[i], tags[angle[0]], tags[angle[1]])
                if a_type in angle_types:
                    angle_types[a_type].append((i, angle))
                else:
                    angle_types[a_type] = [(i, angle)]

        raise NotImplementedError("Too lazy to add angles, harass me if you need it")


    def write_dihedrals(self):
        """Deprecated before it was even written :("""
        raise NotImplementedError("Too lazy to add dihedrals, harass me if you need it")

    def write_impropers(self):
        """Deprecated before it was even written :("""
        raise NotImplementedError("Harass me if you need this.")


class MolInput:
    """
    Class for writing simple molecule files in lammps for deepmd.

    TODO: add bonds, charges, etc. for future applications

    Args:
        atoms (ase.Atoms): Atoms object of molecule to write.

        type_dict (dict): map atom type index to element symbol
                   (Element_tag to specify multiple types of same element)
                   e.g., {1: 'O', 2: 'Si', 3: 'O_h2o', 4: 'H_h2o'}

        name (str): Name of molecule for saving file (mol.name)
    """
    def __init__(self, atoms, type_dict, name="mol"):
        self.atoms = atoms
        self.type_dict = type_dict
        self.name = name

    def write(self):
        self.write_atoms()
        moltemp = MolTemplate(f"mol.{self.name}", self)
        moltemp.write()

    def write_atoms(self):
        self.natoms = len(self.atoms)
        coords = "Coords\n\n"
        types = "Types\n\n"

        for a, (x, y, z) in zip(self.atoms, self.atoms.positions):
            coords += f"{a.index + 1}\t\t{x}\t{y}\t{z}\n"
            types += f"{a.index + 1}\t\t{a.tag}\n"

        self.coords = coords
        self.types = types


class Template:
    """
    Base class for writing lammps data and input files. Replaces all <attr> sections
    in subclass self.text with corresponding LammpsInput instance attributes that contain
    strings for each section.

    Args:
        file_name (str): Name of file to write, generally name.data or in.name.
        lammps_input (LammpsInput instance): LammpsInput object with str attributes used
            to fill in self.text with appropriate commands / values.
    """
    def __init__(self, file_name, lammps_input):
        self.file_name = file_name
        self.input = lammps_input

    def write(self):
        """
        Write lammps file to current directory.
        """
        self.fill()
        self.trim()
        with open(self.file_name, "w") as file:
            file.write(self.text)

    def fill(self):
        """
        Replaces <attr> sections in self.text with corresponding LammpsInput object attribute text.
        """
        pattern = r"<\w+>"
        matches = re.findall(pattern, self.text)
        for match in matches:
            key = match[1:-1]
            attr = getattr(self.input, key)
            attr = str(attr) if attr is not None else ""
            self.text = self.text.replace(match, attr)

    def trim(self):
        """
        Remove unneccessary blank lines from self.text caused by inserting empty strings
        as commands.
        """
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

        Atoms # <atom_style_hint>

        <coords>

        <bonds>

        <angles>

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

        box tilt\tlarge
        read_data\tdata.<name>

        <constraints>

        <pair_coeff>

        <bond_coeff>

        <angle_coeff>

        <kspace_style>

        <groups>
        thermo_style custom step temp etotal pe press pxx pyy pzz pxy pxz pyz lx ly lz vol
        ''')


class MolTemplate(Template):
    text = dedent('''
        <natoms> atoms
        0 bonds
        0 angles

        <coords>

        <types>
        ''')

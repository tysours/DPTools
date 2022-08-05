import numpy as np
import lammps
from dptools.simulate.lammps_io import LammpsInput
from ase.calculators.calculator import (
    Calculator, all_changes, PropertyNotImplementedError
)
from ase.units import GPa
#from dptools.utils import graph2typemap

class LmpCalc(Calculator):
    """
    Base class for lammps ASE calculator
    """

    name = "Lammps"
    implemented_properties = ["energy", "forces", "stress"]

    def __init__(self, 
                 type_map=None,
                 minimize=False, 
                 relax_UC=False,
                 ftol=1e-3,
                 lmp=None, 
                 run_command=None, 
                 verbose=False, 
                 label="lamp", 
                 **kwargs):

        Calculator.__init__(self, label=label, **kwargs)

        if lmp is None:
            if verbose:
                lmp = lammps.lammps()
            else:
                lmp = lammps.lammps(cmdargs="-screen none".split())

        if type_map is not None:
            self._type_map = type_map
        if run_command is None:
            run_command = ["run 0"]
        elif isinstance(run_command, str):
            run_command = [run_command]
        if relax_UC:
            minimize = True
        self.lmp = lmp
        self.minimize = minimize
        self.relax_UC = relax_UC
        self.ftol = ftol
        self.run_command = run_command

    def calculate(self, 
                  atoms=None, 
                  properties=["energy", "forces", "stress"],
                  system_changes=all_changes):
        """
        Parameters
        ----------
        atoms : Optional[Atoms], optional
            atoms object to run the calculation on, by default None
        properties : List[str], optional
            unused, only for function signature compatibility,
        system_changes : List[str], optional
            unused, only for function signature compatibility, by default all_changes
        """
        if atoms is not None:
            self.atoms = atoms.copy()

        # XXX: Is there a better way to do this? Always write input or no?
        self.write_input(atoms)

        if self.minimize:
            self.lmp.command(f"minimize 0.0 {self.ftol} 10000 100000")
        else:
            for comm in self.run_command:
                self.lmp.command(comm)

        # lammps is annoying and jumbles up indices sometimes
        ids = self.lmp.numpy.extract_atom("id").T[0]
        self._sort = np.argsort(ids)

        self.update_atoms(atoms)
        energy = self.lmp.get_thermo("etotal")
        forces = self.lmp.numpy.extract_atom("f")[self._sort]
        stress = self.read_stress()
        self.results["energy"] = energy
        self.results["forces"] = forces
        self.results["stress"] = stress

    def update_atoms(self, atoms):
        positions = self.lmp.numpy.extract_atom("x")[self._sort]
        # shift positions to align with cell at origin
        shift = np.array([self.lmp.get_thermo(l) for l in ["xlo", "ylo", "zlo"]])
        atoms.positions = positions - shift
        atoms.cell = self.read_cell()

    def read_stress(self):
        pxx = self.lmp.get_thermo("pxx") * 1e-3 # kBar
        pyy = self.lmp.get_thermo("pyy") * 1e-3
        pzz = self.lmp.get_thermo("pzz") * 1e-3
        pxy = self.lmp.get_thermo("pxy") * 1e-3
        pyz = self.lmp.get_thermo("pyz") * 1e-3
        pxz = self.lmp.get_thermo("pxz") * 1e-3
        stress = -np.array([pxx, pyy, pzz, pyz, pxz, pxy]) * 1e-1 * GPa
        return stress

    def read_cell(self):
        a = self.lmp.get_thermo("cella")
        b = self.lmp.get_thermo("cellb")
        c = self.lmp.get_thermo("cellc")
        alpha = self.lmp.get_thermo("cellalpha")
        beta = self.lmp.get_thermo("cellbeta")
        gamma = self.lmp.get_thermo("cellgamma")
        return [a, b, c, alpha, beta, gamma]

    def write_input(self):
        """System / forcefield specific"""
        pass


class DeepMD(LmpCalc):
    name = "DP"
    implemented_properties = ["energy", "forces", "stress"]
    def __init__(self, 
                 graph,
                 type_map=None,
                 minimize=False, 
                 relax_UC=False,
                 ftol=1e-3,
                 lmp=None, 
                 run_command=None, 
                 verbose=False, 
                 label="lamp", 
                 **kwargs):

        super().__init__(
                       type_map=type_map,
                       minimize=minimize, 
                       relax_UC=relax_UC,
                       ftol=ftol,
                       lmp=lmp, 
                       run_command=run_command, 
                       verbose=verbose, 
                       label=label, 
                       **kwargs
                       )

        self.graph = graph
        self.style = f'deepmd {self.graph}'

    def set_atoms(self, atoms=None):
        self.set_types(atoms)
        #if 0 in atoms.get_tags():
        for a in atoms:
            a.tag = self._type_map[a.symbol]

    def set_charges(self):
        self.charges = np.zeros(len(self.atoms))

    def set_types(self, atoms=None):
        if atoms is None:
            atoms = self.atoms

        if not hasattr(self, '_type_map'):
            raise NotImplementedError("Automatic detection of type_map not working, "
                        "please manually specify type_map")

            # TODO: Figure out why this fails, need to manually specify type_map until then
            # Automatically determines type_map from self.graph
            #from deepmd import DeepPotential
            #dp = DeepPotential(self.graph)
            #type_map = {sym: i for i, sym in enumerate(dp.get_type_map())}
            self._type_map = graph2typemap(self.graph)

        # lammps type indexing needs to start at 1, not 0
        if 0 in self._type_map.values():
            self._type_map = {sym: i + 1 for sym, i in self._type_map.items()}
        #for a in atoms:
        #    a.tag = self._type_map[a.symbol]

        # need to invert dict for lammps_io - a bit confusing, probably rework
        self.types = {v: k for k, v in self._type_map.items()} 

    def set_coeffs(self):
        self.coeffs = None
        self.pair_coeffs = None

    def write_input(self, atoms=None):
        # XXX maybe add this to base class if identical for other FFs too
        if atoms is not None:
            self.atoms = atoms
        self.set_atoms(atoms)
        self.set_charges()
        self.set_coeffs()
        self.io = LammpsInput(self.atoms, 
                              self.types, 
                              charges=self.charges,
                              pair_style=self.style,
                              coeffs=self.coeffs,
                              kspace_style=None,
                              pair_coeffs=self.pair_coeffs)

        self.io.write_atoms(self.atoms)
        self.io.write_input()
        self.lmp.command("clear")
        self.lmp.file("in.atoms")
        if self.relax_UC:
            self.lmp.command("fix 1 all box/relax tri 1.0")


class ClayFF(LmpCalc):
    """class for the classical ClayFF force field. Unused for deepmd but I will leave it here for future reference"""
    name = "ClayFF"
    implemented_properties = ["energy", "forces", "stress"]
    def __init__(self, 
                 type_map=None,
                 minimize=False, 
                 relax_UC=False,
                 ftol=1e-3,
                 lmp=None, 
                 run_command=None, 
                 verbose=False, 
                 label="lamp", 
                 cutoff=12.0,
                 **kwargs):

        super().__init__(
                       type_map=type_map,
                       minimize=minimize, 
                       relax_UC=relax_UC,
                       ftol=ftol,
                       lmp=lmp, 
                       run_command=run_command, 
                       verbose=verbose, 
                       label=label, 
                       **kwargs
                       )

        self.rc = cutoff
        self.style = f'lj/cut/coul/long {self.rc}'

    def set_atoms(self, atoms=None):
        if not hasattr(self, '_type_map'):
            self.set_types(atoms)
        if 0 in atoms.get_tags():
            for a in atoms:
                a.tag = self._type_map[a.symbol]
        #lengths = atoms.cell.lengths()
        #repeat = [int((self.rc * 2) // l + 1) for l in lengths]
        #if hasattr(self, 'repeat'):
        #    if repeat != self.repeat:
        #        raise Exception("REPEAT CHANGED, FIX IT OR FIX LOSS FCN")
        #self.repeat = repeat 
        #atoms = atoms.repeat(self.repeat)
        #self.atoms = atoms

    def set_charges(self):
        q_vals = {'Si': 2.1, 'O': -1.05}
        charges = [q_vals[a.symbol] for a in self.atoms]
        self.charges = np.array(charges)

    def set_types(self, atoms=None):
        if atoms is None:
            atoms = self.atoms
        symbols = np.unique(atoms.get_chemical_symbols())
        types = {s: i + 1 for i, s in enumerate(symbols)}
        for a in atoms:
            a.tag = types[a.symbol]
        self._type_map = types
        self.types = {v: k for k, v in types.items()} # inverting dict, probably stupid

    def set_coeffs(self):
        epsilon = {'Si': 7.981163385703463e-08, 'O': 0.006738781799175867}
        sigma = {'Si': 3.302027, 'O': 3.165541}
        self.coeffs = {k: {'eps': epsilon[v], 'sig': sigma[v]}
                        for k, v in self.types.items()}

    def write_input(self, atoms=None):
        if atoms is not None:
            self.atoms = atoms
        self._check_cell()
        self.set_atoms(atoms)
        self.set_charges()
        self.set_coeffs()
        self.io = LammpsInput(self.atoms, 
                              self.types, 
                              charges=self.charges,
                              pair_style=self.style,
                              coeffs=self.coeffs,
                              cutoff=self.rc)

        self.io.write_atoms(self.atoms)
        self.io.write_input()
        self.lmp.command('clear')
        self.lmp.file('in.atoms')
        if self.relax_UC:
            self.lmp.command('fix 1 all box/relax tri 1.0')

    def _check_cell(self):
        '''Checks if lattice constants are > 2 * cutoff'''
        min_lc = min(self.atoms.cell.lengths())
        if min_lc < 2 * self.rc:
            raise Exception("Lattice constant < 2 * cutoff\nRepeat Atoms or decrease cutoff")
        return


class BKS(LmpCalc):
    """class for the classical BKS force field. Unused for deepmd but I will leave it here for future reference"""
    #raise 
    name = "BKS"
    implemented_properties = ["energy", "forces", "stress"]
    def __init__(self, 
                 type_map=None,
                 minimize=False, 
                 relax_UC=False,
                 ftol=1e-3,
                 lmp=None, 
                 run_command=None, 
                 verbose=False, 
                 label="lamp", 
                 cutoff=12.0,
                 **kwargs):

        super().__init__(
                       type_map=type_map,
                       minimize=minimize, 
                       relax_UC=relax_UC,
                       ftol=ftol,
                       lmp=lmp, 
                       run_command=run_command, 
                       verbose=verbose, 
                       label=label, 
                       **kwargs
                       )

        self.rc = cutoff
        self.style = f'buck/coul/long {self.rc}'

    def set_atoms(self, atoms=None):
        if not hasattr(self, '_type_map'):
            self.set_types(atoms)
        if 0 in atoms.get_tags():
            for a in atoms:
                a.tag = self._type_map[a.symbol]
        #lengths = atoms.cell.lengths()
        #repeat = [int((self.rc * 2) // l + 1) for l in lengths]
        #if hasattr(self, 'repeat'):
        #    if repeat != self.repeat:
        #        raise Exception("REPEAT CHANGED, FIX IT OR FIX LOSS FCN")
        #self.repeat = repeat 
        #atoms = atoms.repeat(self.repeat)
        #self.atoms = atoms

    def set_charges(self):
        q_vals = {'Si': 2.4, 'O': -1.2}
        charges = [q_vals[a.symbol] for a in self.atoms]
        self.charges = np.array(charges)

    def set_types(self, atoms=None):
        if atoms is None:
            atoms = self.atoms
        symbols = np.unique(atoms.get_chemical_symbols())
        types = {s: i + 1 for i, s in enumerate(symbols)}
        for a in atoms:
            a.tag = types[a.symbol]
        self._type_map = types
        self.types = {v: k for k, v in types.items()} # inverting dict, probably stupid

    def set_coeffs(self):
        self.coeffs = None

        Aij = {'Si-O': 18003.7572, 'O-O': 1388.7730, 'Si-Si': 0.0}
        bij = {'Si-O': 1 / 4.87318, 'O-O': 1 / 2.760, 'Si-Si': 1.0}
        cij = {'Si-O': 133.5381, 'O-O': 175.000, 'Si-Si': 0.0}

        pair_coeffs = ""
        for k in Aij:
            ij = [self._type_map[k.split('-')[0]], self._type_map[k.split('-')[1]]]
            if ij[0] > ij[1]:
                ij.reverse()
            pair_coeffs += f"pair_coeff {ij[0]} {ij[1]} {Aij[k]} {bij[k]} {cij[k]}\n"

        self.pair_coeffs = pair_coeffs

    def write_input(self, atoms=None):
        # XXX maybe add this to base class if identical for other FFs too
        if atoms is not None:
            self.atoms = atoms
        self._check_cell()
        self.set_atoms(atoms)
        self.set_charges()
        self.set_coeffs()
        self.io = LammpsInput(self.atoms, 
                              self.types, 
                              charges=self.charges,
                              pair_style=self.style,
                              coeffs=self.coeffs,
                              pair_coeffs=self.pair_coeffs,
                              cutoff=self.rc)

        self.io.write_atoms(self.atoms)
        self.io.write_input()
        self.lmp.command('clear')
        self.lmp.file('in.atoms')
        if self.relax_UC:
            self.lmp.command('fix 1 all box/relax tri 1.0')

    def _check_cell(self):
        '''Checks if lattice constants are > 2 * cutoff'''
        min_lc = min(self.atoms.cell.lengths())
        if min_lc < 2 * self.rc:
            raise Exception("Lattice constant < 2 * cutoff\nRepeat Atoms or decrease cutoff")
        return

import os
import numpy as np
from ase import units
from ase.io import read, write

from dptools.simulate.calculator import DeepMD
from dptools.simulate.lammps_io import MolInput
from dptools.utils import read_dump, columnize
from dptools.utils import get_seed as seed


class Simulation:
    """
    Base class for setting up, running, and processing specific simulations in LAMMPS
    using DP models for energy and force evaluations.

    Args:
        atoms (str, ase.Atoms, or list[ase.Atoms]): Input structure(s) to run
            simulation with. ase.Atoms object or str with path to .traj (or similar) file.

        graph (str): Path to deepmd model .pb file

        type_map (dict): Dictionary that maps elemental symbol keys to type index values.

        path (str): Path to directory to write results to if dir other than $PWD desired.

        **kwargs: Simulation specific kwargs to pass to setup and get_commands methods.
    """

    def __init__(self, atoms, graph, type_map, file_out="atoms.traj", path="./", **kwargs):
        if isinstance(atoms, str):
            atoms = [read(atoms)]
        elif not isinstance(atoms, list):
            atoms = [atoms]
        self.atoms = atoms
        self.graph = graph
        self.type_map = type_map
        self.path = path
        self.file_out = os.path.join(path, file_out)
        self.setup(**kwargs)

    def setup(self, **kwargs):
        """
        Simulation specific method to do any needed setup before running (e.g., cell deformations).
        Must call self.get_commands() method.
        """
        self.commands = self.get_commands(**kwargs)

    def run(self, process=True, commands=None, file_out=None):
        """
        Runs simulation after setting everything up.

        Args:
            process (bool): If True calls self.process() method after running.

            commands (list[str], optional): List of lammps commands if different from self.commands.
                Rarely used, should set self.commands in self.setup() generally.

            file_out (optional): Name of output file if different from self.file_out for
                whatever reason. Also rarely used.
        """
        commands = commands if commands else self.commands
        for atoms in self.atoms:
            calc = DeepMD(self.graph, type_map=self.type_map, run_command=commands, verbose=True)
            atoms.calc = calc
            atoms.get_potential_energy()
        if process:
            self.process(file_out=file_out)

    def process(self, file_out=None):
        """Simulation specific method to process and write results after calculation."""
        file_out = file_out if file_out else self.file_out
        write(file_out, self.atoms)

    def pre_opt(self, nsw, cell=False, ftol=0.01):
        """
        Run quick optimization on structure before running full simulation.

        Args:
            nsw (int): Max number of optimization steps to run.
            cell (bool): Optimize unit cell if True, else only positions.
            ftol (float): Max force convergence tolerance criterion.
        """
        Opts = {0: Opt, 1: CellOpt}
        commands = Opts[cell].get_commands(self, nsw=nsw, ftol=ftol)

        Simulation.run(self, process=False, commands=commands)

        file_out = os.path.join(self.path, "pre_opt.traj")
        write(file_out, self.atoms)

    def _warn_unused(self, **kwargs):
        for k, v in kwargs.items():
            print(f"WARNING: {k}={v} unused for calculation type {self.calc_type}")

    def write_array(self, data):
        name = f"data.{self.calc_type}.npy"
        np.save(os.path.join(self.path, name), data)


class NewSimulation(Simulation):
    """
    Template/example for making new simulation types in lammps.

    Args:
        setup_arg1: Argument from params.yaml that is passed to setup method
        setup_arg2: Argument from params.yaml that is passed to setup method
        param_arg1: Argument from params.yaml that is passed to get_commands method
        param_arg2: Argument from params.yaml that is passed to get_commands method
    """

    def setup(self, setup_arg1=None, setup_arg2=None, **kwargs):
        """
        Simulation specific method to do any needed setup before running (e.g., cell deformations).
        Must call self.get_commands() method.
        """

        # do stuff with setup args here

        # then set commands
        self.commands = self.get_commands(**kwargs)

    def get_commands(self, **kwargs):
        self._warn_unused(**kwargs) # warn about any unused kwargs from params.yaml

        # set all simulation lammps commands (besides initial setup, e.g. unit styles)
        commands = ["run 0"]
        return commands

    def run(self, file_out=None):
        """
        Rarely need subclass run method. Test without it and if Simulation.run fails
        for whatever reason, write your own run method.
        """
        pass

    def process(self, file_out=None):
        """
        Only needed if additional proceessing from lammps output is necessary.
        Also useful for printing results summaries.
        """
        pass


class SPE(Simulation):
    """Simple single point energy calculation, not much to it."""
    calc_type = "spe"

    def get_commands(self, **kwargs):
        self._warn_unused(**kwargs)
        commands = ["run 0"]
        return commands


class Opt(Simulation):
    calc_type = "opt"

    def get_commands(self, nsw=1000, ftol=1e-2, etol=0.0, disp_freq=10, **kwargs):
        self._warn_unused(**kwargs)
        commands = [
            f"thermo {disp_freq}",
             "min_modify norm max",
            f"minimize {etol} {ftol} {nsw} {nsw * 10}",
            ]
        return commands


class CellOpt(Simulation):
    calc_type = "cellopt"

    def get_commands(self, nsw=1000, ftol=1e-2, etol=0.0, opt_type="aniso", Ptarget=0.0, disp_freq=10, **kwargs):
        self._warn_unused(**kwargs)
        commands = [
                f"thermo {disp_freq}",
                 "min_modify norm max",
                f"fix cellopt all box/relax {opt_type} {Ptarget}",
                f"minimize {etol} {ftol} {nsw} {nsw * 10}",
                 "unfix cellopt",
                ]
        return commands


class NVT(Simulation):
    calc_type = "nvt-md"

    def setup(self, pre_opt=True, **kwargs):
        if pre_opt:
            self.pre_opt(200)

        self.commands = self.get_commands(**kwargs)

    def get_commands(self, steps=10000, timestep=0.5, Ti=298.0, Tf=298.0, equil_steps=1000, write_freq=100, disp_freq=100, **kwargs):
        self._warn_unused(**kwargs)
        timestep = timestep * 1e-3 # convert to ps for lammps
        commands = [
            f"thermo {disp_freq}",
            f"variable\tdt\tequal\t0.5e-3",
            "variable\ttdamp\tequal 100*${dt}",
            "run_style verlet",
            "timestep ${dt}",
            # XXX: Add customizable velocity keywords as args?
            f"velocity all create {Ti} {seed()} rot yes mom yes dist gaussian",
            f"fix equil all nvt temp {Ti} {Ti} ${{tdamp}}",
            f"run {equil_steps}",
             "unfix equil",
            f"fix nvt_prod all nvt temp {Ti} {Tf} ${{tdamp}}",
            f"dump 1 all custom {write_freq} nvt.dump id type x y z",
            f"run {steps}"
            ]
        return commands

    def process(self, file_out=None):
        atoms = read_dump("nvt.dump", self.type_map)
        write(self.file_out, atoms)


class NPT(Simulation):
    calc_type = "npt-md"

    def setup(self, pre_opt=True, **kwargs):
        if pre_opt:
            self.pre_opt(200, cell=True)

        self.commands = self.get_commands(**kwargs)

    def get_commands(self, steps=10000, timestep=0.5, Pi=0.0, Pf=0.0, Ti=298.0, Tf=298.0, equil_steps=1000, write_freq=100, disp_freq=100, **kwargs):
        self._warn_unused(**kwargs)
        timestep = timestep * 1e-3 # convert to ps for lammps
        commands = [
            f"thermo {disp_freq}",
            f"variable\tdt\tequal\t0.5e-3",
            "variable\tpdamp\tequal 1000*${dt}",
            "variable\ttdamp\tequal 100*${dt}",
            "run_style verlet",
            "timestep ${dt}",
            # XXX: Add customizable velocity keywords as args?
            f"velocity all create {Ti} {seed()} rot yes mom yes dist gaussian",
            f"fix equil all npt temp {Ti} {Ti} ${{tdamp}} tri {Pi} {Pi} ${{pdamp}}",
            f"run {equil_steps}",
             "unfix equil",
            f"fix npt_prod all npt temp {Ti} {Tf} ${{tdamp}} tri {Pi} {Pf} ${{pdamp}}",
            f"dump 1 all custom {write_freq} npt.dump id type x y z",
            f"run {steps}"
            ]
        return commands

    def process(self, file_out=None):
        atoms = read_dump("npt.dump", self.type_map)
        write(self.file_out, atoms)


class EOS(Simulation):
    calc_type = "eos"

    def setup(self, N=5, lo=0.96, hi=1.04, pre_opt=True, **kwargs):
        if pre_opt:
            self.pre_opt(200, cell=True)

        self.set_volumes(lo, hi, N)

        self.commands = self.get_commands(**kwargs)

    def get_commands(self, nsw=300, ftol=1e-3, etol=0.0, disp_freq=10, **kwargs):
        self._warn_unused(**kwargs)

        # only need to run standard optimizations on each cell volume
        commands = Opt.get_commands(self, nsw=nsw, ftol=ftol, etol=etol, disp_freq=disp_freq)
        return commands

    def set_volumes(self, lo, hi, N):
        atoms, = self.atoms.copy()
        self.atoms = []
        for v in np.linspace(lo, hi, N):
            new_atoms = atoms.copy()
            new_cell = atoms.cell.array * v ** (1 / 3)
            new_atoms.set_cell(new_cell, scale_atoms=True)
            self.atoms.append(new_atoms)

    def process(self, file_out=None):
        from ase.eos import EquationOfState
        volumes = [a.get_volume() for a in self.atoms]
        energies = [a.get_potential_energy() for a in self.atoms]

        # TODO: Add optional arg to change eos type
        eos = EquationOfState(volumes, energies, eos='birchmurnaghan')
        try:
            v0, e0, B = eos.fit()
            bulk_mod = B / units.kJ * 1.0e24 # [GPa]
            print(f"BULK MODULUS: {bulk_mod:.3f} GPa")
        except RuntimeError:
            print("Bad EOS fit, can not determined bulk modulus")
            print("Check energy versus volume data in data.eos.npy")

        write(self.file_out, self.atoms)
        eos_data = columnize(volumes, energies)
        self.write_array(eos_data)


class Vib(Simulation):
    calc_type = "vib"

    def setup(self, pre_opt=True, **kwargs):
        if pre_opt:
            # tight ftol convergence for vib to ensure minimum is reached
            self.pre_opt(200, ftol=0.001)

        self.commands = self.get_commands(**kwargs)

    def set_displacements(self, nfree, delta):
        # NOTE: deprecated, way more efficient to just use
        #       lammps built in dynamical_matrix command
        if nfree not in [2, 4]:
            raise ValueError("Only supports nfree = 2 or 4")
        atoms, = self.atoms.copy()

        displacements = [-1, 1, -2, 2]
        n_displacements = 3 * nfree * len(atoms)

        for a in atoms:
            for j in range(3): # xyz directions
                for i in range(nfree):
                    d = displacements[i] * delta # magnitude of displacement to translate each atom
                    new_atoms = atoms.copy()
                    new_atoms[a.index].position[j] += d
                    self.atoms.append(new_atoms)

    def get_commands(self, delta=0.015, **kwargs):
        self._warn_unused(**kwargs)
        # calculate dynamical matrix / mass weighted hessian
        commands = [f"dynamical_matrix all eskm {delta} file dynmat.dat"]
        return commands

    def run(self):
        atoms, = self.atoms
        calc = DeepMD(self.graph,
                      type_map=self.type_map,
                      run_command=self.commands,
                      verbose=True,
                      )

        # Need to not update results or lammps crashes, and no reason to write
        # results to Atoms object anyway since we only care about dynmat.dat file
        calc.calculate(atoms, update=False)
        self.process()

    def process(self):
        dyn_mat = np.loadtxt("dynmat.dat")
        n = len(self.atoms[0])
        # reshape lammps dynammical matrix output to square (3n x 3n)
        dyn_mat = dyn_mat.reshape(3 * n, 3 * n)

        eig_vals, eig_vecs = np.linalg.eig(dyn_mat)
        eig_vals = np.flip(np.sort(eig_vals))
        imag_filt = np.array([-1 if e < 0 else 1 for e in eig_vals])

        # speed of light [m/s] https://physics.nist.gov/cgi-bin/cuu/Value?c
        c = 299792458.0
        conversion = 1e12 / (c * 100) # Hz --> cm-1
        freq = np.sqrt(np.abs(eig_vals)) / (2 * np.pi) * conversion
        freq *= imag_filt # save imaginary frequencies as negative

        self.write_array(freq)

        for j, f in enumerate(freq):
            i = "i" if f < 0 else ""
            print(f"Mode {j}: {abs(f):.2f}{i}")


class GCMC(Simulation):
    """Grand-canonical monte carlo simulation."""
    calc_type = "gcmc"

    def setup(self, molecule="H2O", pre_opt=False, pre_opt_mol=False, **kwargs):
        if os.path.isfile(molecule):
            mol = read(molecule)
        else:
            from ase import build
            mol = build.molecule(molecule)
        if mol.cell.sum() == 0.0: # need cell or lammps crashes
            mol.cell = self.atoms[0].cell.copy()
            mol.center()

        mol_tags = [self.type_map[m.symbol] + 1 for m in mol] # tag types for lammps mol writer
        mol.set_tags(mol_tags)

        self._mol = mol.get_chemical_formula().lower() # save for naming files

        if pre_opt_mol:
            optmol = Opt(mol,
                         self.graph,
                         self.type_map,
                         file_out=f"{self._mol}.traj",
                         path=self.path,
                         nsw=200,
                         )
            optmol.run()

        molin = MolInput(mol, self.type_map, name=self._mol)
        molin.write() # write lammps molecule file

        if pre_opt:
            self.pre_opt(200, cell=True)

        self.commands = self.get_commands(**kwargs)

    def get_commands(self, steps=100, n_ex=10, n_mc=10, T=298.0, P=1.0, dmax=1.0, equil_steps=0, write_freq=1, disp_freq=5, **kwargs):
        self._warn_unused(**kwargs)

        commands = [
                "compute_modify  thermo_temp dynamic/dof yes",
                f"molecule mol mol.{self._mol}",
                f"group {self._mol} molecule 0",
                f"fix dpgcmc {self._mol} gcmc 1 {n_ex} {n_mc} 0 {seed()} "\
                        f"{T} 0.0 {dmax} mol mol pressure {P} full_energy",
                f"thermo {disp_freq}",
                f"run {equil_steps}",
                f"dump 1 all custom {write_freq} gcmc.dump id type x y z",
                f"run {steps}",
                ]

        return commands

    def process(self, file_out=None):
        atoms = read_dump("gcmc.dump", self.type_map)
        write(self.file_out, atoms)


Simulations = {
    "spe": SPE,
    "opt": Opt,
    "cellopt": CellOpt,
    "nvt-md": NVT,
    "npt-md": NPT,
    "eos": EOS,
    "vib": Vib,
    "gcmc": GCMC,
}

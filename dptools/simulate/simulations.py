from ase.io import read, write
import os

from dptools.simulate.calculator import DeepMD
from dptools.simulate.parameters import get_parameter_sets
from dptools.utils import read_type_map, read_dump
from dptools.utils import get_seed as seed
from dptools.cli import BaseCLI


class Simulation:
    def __init__(self, atoms, graph, type_map, file_out="atoms.traj", path="./", **kwargs):
        if isinstance(atoms, str):
            atoms = read(atoms)
        self.atoms = atoms
        self.graph = graph
        self.type_map = type_map
        self.file_out = os.path.join(path, file_out)
        self.commands = self.get_commands(**kwargs)

    def run(self, process=True):
        calc = DeepMD(self.graph, type_map=self.type_map, run_command=self.commands, verbose=True)
        self.atoms.calc = calc
        self.atoms.get_potential_energy()
        if process:
            self.process()

    def process(self):
        """Simulation specific method to process and write results after calculation"""
        write(self.file_out, self.atoms)

    def _warn_unused(self, **kwargs):
        for k, v in kwargs.items():
            print(f"WARNING: {k}={v} unused for calculation type {self.calc_type}")


class SPE(Simulation):
    calc_type = "spe"

    def get_commands(self, **kwargs):
        self._warn_unused(**kwargs)
        commands = ["run 0"]
        return commands

class Opt(Simulation):
    calc_type = "opt"

    def get_commands(self, nsw=1000, ftol=1e-3, etol=0.0, disp_freq=10, **kwargs):
        self._warn_unused(**kwargs)
        commands = [
            f"thermo {disp_freq}",
            f"minimize {etol} {ftol} {nsw} {nsw * 10}",
            ]
        return commands

class CellOpt(Simulation):
    calc_type = "cellopt"

    def get_commands(self, nsw=1000, ftol=1e-3, etol=0.0, opt_type="aniso", Ptarget=0.0, disp_freq=10, **kwargs):
        self._warn_unused(**kwargs)
        commands = [
                f"thermo {disp_freq}",
                f"fix cellopt all box/relax {opt_type} {Ptarget}",
                f"minimize {etol} {ftol} {nsw} {nsw * 10}",
                 "unfix cellopt",
                ]
        return commands

class NVT(Simulation):
    calc_type = "nvt-md"

    def get_commands(self, steps=1000, timestep=0.5, Ti=298.0, Tf=298.0, equil_steps=1000, write_freq=100, disp_freq=100, pre_opt=True, **kwargs):
        self._warn_unused(**kwargs)
        commands = []
        if pre_opt:
            commands += Opt.get_commands(self, nsw=200)
        timestep = timestep * 1e-3 # convert to ps for lammps
        commands += [
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

    def process(self):
        atoms = read_dump("nvt.dump", self.type_map)
        write(self.file_out, atoms)


class NPT(Simulation):
    calc_type = "npt-md"

    def get_commands(self, steps=1000, timestep=0.5, Pi=0.0, Pf=0.0, Ti=298.0, Tf=298.0, equil_steps=1000, write_freq=100, disp_freq=100, pre_opt=True, **kwargs):
        self._warn_unused(**kwargs)
        commands = []
        if pre_opt:
            commands += CellOpt.get_commands(self, nsw=300)
        timestep = timestep * 1e-3 # convert to ps for lammps
        commands += [
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

    def process(self):
        atoms = read_dump("npt.dump", self.type_map)
        write(self.file_out, atoms)

Simulations = {"spe": SPE, "opt": Opt, "cellopt": CellOpt, "nvt-md": NVT, "npt-md": NPT}

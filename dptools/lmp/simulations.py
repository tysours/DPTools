from ruamel.yaml import YAML
from ase.io import read
import os

from dptools.lmp.calculator import DeepMD
from dptools.lmp.parameters import get_parameter_sets
from dptools.utils import read_type_map
from dptools.utils import get_seed as seed
from dptools.env import get_dpfaults
from dptools.cli import BaseCLI

class Simulation:
    def __init__(self, atoms, graph, type_map, file_out="atoms.traj", path="./", **kwargs):
        self.atoms = atoms
        self.graph = graph
        self.type_map = type_map
        self.file_out = file_out
        self.path = path
        self.commands = self.get_commands(**kwargs)

    def run(self):
        calc = DeepMD(self.graph, type_map=self.type_map, run_command=self.commands)
        self.atoms.calc = calc
        self.atoms.get_potential_energy()
        self.process()

    def process(self):
        """Simulation specific method to process and write results after calculation"""
        self.atoms.write(self.file_out)


class SPE(Simulation):
    @staticmethod
    def get_commands():
        commands = ["run 0"]
        return commands

class Opt(Simulation):
    @staticmethod
    def get_commands(nsw=1000, ftol=1e-3, etol=0.0):
        commands = [f"minimize {etol} {ftol} {nsw} {nsw * 10}"]
        return commands

class CellOpt(Simulation):
    @staticmethod
    def get_commands(nsw=1000, ftol=1e-3, etol=0.0, opt_type="aniso", Ptarget=0.0):
        commands = [
                f"fix cellopt all box/relax {opt_type} {Ptarget}",
                f"minimize {etol} {ftol} {nsw} {nsw * 10}",
                 "unfix cellopt",
                ]
        return commands

class NVT(Simulation):
    @staticmethod
    def get_commands(steps=1000, timestep=0.5, Ti=298.0, Tf=298.0, equil_steps=1000, write_freq=100, disp_freq=100, pre_opt=True):
        commands = [f"thermo {disp_freq}"]
        timestep = timestep * 1e-3 # convert to ps for lammps
        if pre_opt:
            commands += Opt.get_commands(nsw=200)
        commands += [
            f"variable\tdtequal\t0.5e-3",
            "variable\ttdamp\tequal 100*${dt}",
            "run_style verlet",
            "timestep ${dt}",
            # XXX: Add customizable velocity keywords as args?
            f"velocity all create {Ti} {seed()} rot yes mom yes dist gaussian",
            f"fix 2 all nvt temp {Ti} {Tf} ${{tdamp}}",
            f"run {equil_steps}",
            f"dump 1 all custom {write_freq} nvt.dump id type x y z",
            f"run {steps}"
            ]

class NPT(Simulation):
    @staticmethod
    def get_commands():
        pass

Simulations = {"spe": SPE, "opt": Opt, "cellopt": CellOpt, "nvt-md": NVT, "npt-md": NPT}

class CLI(BaseCLI):
    def add_args(self):
        self.parser.add_argument(
            "calculation",
            nargs=1,
            type=str,
            help="Type of calculation to run (spe, opt, cellopt, nvt-md, npt-md, or params.yaml)"
        )
        self.parser.add_argument(
            "structure",
            nargs=1,
            help="File containing structure to run calculation on (.traj, .xyz, .cif, etc.)"
        )
        graph_default, map_default = get_dpfaults()
        self.parser.add_argument("-m", "--model", nargs=1, type=str, default=graph_default,
                help="Specify path of frozen .pb deepmd model to use")
        self.parser.add_argument("-t", "--type-map", nargs=1, type=str, default=map_default,
                help="Specify path of type_map.json to use")
        self.parser.add_argument("-p", "--path", nargs=1, type=str, default="./",
                help="Specify path to write simulation files and results to")
        self.parser.add_argument("-o", "--output", nargs=1, type=str, default="atoms.traj",
                help="Name of file to write calculation output to")
        self.parser.add_argument("-g", "--generate-input", nargs=1, type=bool, default=False,
                help="Only setup calculation and generate input files but do not run calculation")

    def main(self, args):
        atoms = read(args.structure[0])
        self.read_params(args.calculation[0])
        sim = Simulations[self.calc_type](
                atoms, 
                args.model, 
                type_map=read_type_map(args.type_map),
                file_out=args.output,
                path=args.path,
                **self.params
                )

        if not args.generate_input:
            sim.run()
        else:
            raise NotImplementedError("Input generation only work in progress, harass me if you need it")

    def read_params(self, calc_arg):
        if calc_arg.endswith(".yaml"):
            with open(calc_arg) as file:
                params = YAML().load(file.read())
        else:
            param_sets = get_parameter_sets()
            params = param_sets[calc_arg]
        self.calc_type = params.pop("type").split(".")[0]
        self.params = params

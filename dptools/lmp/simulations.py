from dptools.lmp.calculator import DeepMD
from dptools.utils import get_dpfaults
from ase.io import read
from dptools.cli import BaseCLI
import os
import json

class Simulation:
    def __init__(self, atoms, graph, type_map=None, file_out="atoms.traj", path="./", **kwargs):
        self.atoms = atoms
        self.graph = graph
        if not type_map:
            from dptools.utils import graph2typemap
            type_map = graph2typemap(self.graph)
        self.type_map = type_map
        self.file_out = file_out
        self.path = path
        #self.params = kwargs
        self.commands = self.get_commands(**kwargs)

    def run(self):
        calc = DeepMD(self.graph, type_map=self.type_map, run_command=self.commands)
        self.atoms.calc = calc
        self.atoms.get_potential_energy()
        self.write_output()

    def write_output(self):
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
    def get_commands(nsw=1000, ftol=1e-3, etol=0.0, opt_type="aniso", P=0.0):
        commands = [
                f"fix cellopt all box/relax {opt_type} {P}",
                f"minimize {etol} {ftol} {nsw} {nsw * 10}",
                 "unfix cellopt",
                ]
        return commands

class NVT(Simulation):
    @staticmethod
    def get_commands():
        pass

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
            help="Type of calculation to run (spe, opt, cellopt, nvt-md, npt-md)"
        )
        self.parser.add_argument(
            "structure",
            nargs=1,
            help="File containing structure to run calculation on (.traj, .xyz, .cif, etc.)"
        )
        graph_default, map_default = get_dpfaults()
        self.parser.add_argument("-m", "--model", nargs=1, type=str, default=graph_default,
                help="Specify path of frozen .pb deepmd model to use")
        self.parser.add_argument("-p", "--path", nargs=1, type=str, default="./",
                help="Specify path to write simulation files and results to")
        self.parser.add_argument("-o", "--output", nargs=1, type=str, default="atoms.traj",
                help="Name of file to write calculation output to")
        self.parser.add_argument("-g", "--generate-input", nargs=1, type=bool, default=False,
                help="Only setup calculation and generate input files but do not run calculation")

    def main(self, args):
        atoms = read(args.structure[0])
        self.read_params()
        sim = Simulations[args.calculation[0]](
                atoms, 
                args.model, 
                file_out=args.output,
                path=args.path,
                **self.params
                )

        if not args.generate_input:
            sim.run()
        else:
            raise NotImplementedError("Input generation only work in progress, harass me if you need it")

    def read_params(self):
        try:
            with open("params.json") as file:
                params = json.loads(file.read())
        except FileNotFoundError:
            params = {}
        self.params = params

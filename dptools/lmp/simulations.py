from ruamel.yaml import YAML
from ase.io import read, write
import os

from dptools.lmp.calculator import DeepMD
from dptools.lmp.parameters import get_parameter_sets
from dptools.utils import read_type_map, read_dump
from dptools.utils import get_seed as seed
from dptools.cli import BaseCLI
from dptools.env import get_dpfaults, set_custom_env


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
    def get_commands(nsw=1000, ftol=1e-3, etol=0.0, disp_freq=10):
        commands = [
            f"thermo {disp_freq}",
            f"minimize {etol} {ftol} {nsw} {nsw * 10}",
            ]
        return commands

class CellOpt(Simulation):
    @staticmethod
    def get_commands(nsw=1000, ftol=1e-3, etol=0.0, opt_type="aniso", Ptarget=0.0, disp_freq=10):
        commands = [
                f"thermo {disp_freq}",
                f"fix cellopt all box/relax {opt_type} {Ptarget}",
                f"minimize {etol} {ftol} {nsw} {nsw * 10}",
                 "unfix cellopt",
                ]
        return commands

class NVT(Simulation):
    @staticmethod
    def get_commands(steps=1000, timestep=0.5, Ti=298.0, Tf=298.0, equil_steps=1000, write_freq=100, disp_freq=100, pre_opt=True):
        commands = []
        if pre_opt:
            commands += Opt.get_commands(nsw=200)
        timestep = timestep * 1e-3 # convert to ps for lammps
        commands += [
            f"thermo {disp_freq}",
            f"variable\tdt\tequal\t0.5e-3",
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
        return commands

    def process(self):
        atoms = read_dump("nvt.dump", self.type_map)
        write(self.file_out, atoms)


class NPT(Simulation):
    @staticmethod
    def get_commands():
        raise NotImplementedError("Harass me if you need this")

Simulations = {"spe": SPE, "opt": Opt, "cellopt": CellOpt, "nvt-md": NVT, "npt-md": NPT}

class CLI(BaseCLI):
    def add_args(self):
        self.parser.add_argument(
            "calculation",
            type=str,
            help="Type of calculation to run (spe, opt, cellopt, nvt-md, npt-md, or params.yaml)",
            #choices=[k for k in Simulations.keys()] + ["path/to/params.yaml"], # messier than help comment IMO
        )
        self.parser.add_argument(   
            "structure",
            nargs=1,    # TODO: Add support for multiple structure inputs
            help="File containing structure to run calculation on (.traj, .xyz, .cif, etc.)"
        )
        self.parser.add_argument("-m", "--model-label", type=str, default=None,
                help="Label of specific model to use (see dptools set -h)")
        self.parser.add_argument("-s", "--submit", action="store_true",
                help="Automatically submit job(s) to train model(s) once input has been created")
        self.parser.add_argument("-g", "--generate-input", action="store_true",
                help="Only setup calculation and generate input files but do not run calculation")
        self.parser.add_argument("-p", "--path", nargs=1, type=str, default="./",
                help="Specify path to write simulation files and results to")
        self.parser.add_argument("-o", "--output", type=str, default="{calculation}.traj",
                help="Name of file to write calculation output to")

    def main(self, args):
        atoms = read(args.structure[0])
        self.structures = [os.path.abspath(s) for s in args.structure]
        self.set_model(args.model_label)
        self.set_params(args.calculation)
        if args.output == "{calculation}.traj": # replace default placeholder name
            args.output = f"{self.calc_type}.traj" 

        sim = Simulations[self.calc_type](
                atoms, 
                self.graph,
                type_map=read_type_map(self.type_map),
                file_out=args.output,
                path=args.path,
                **self.params
                )

        if args.submit:
            self.submit_jobs(args.path)
        elif args.generate_input:
            raise NotImplementedError("--generate-input work in progress, harass me if you need it")
        else:
            sim.run()

    def set_params(self, calc_arg):
        if calc_arg.endswith(".yaml"):
            calc_arg = os.path.abspath(calc_arg)
            with open(calc_arg) as file:
                params = YAML().load(file.read())
        else:
            param_sets = get_parameter_sets()
            params = param_sets[calc_arg]
        self.calc_type = params.pop("type").split(".")[0]
        self.params = params
        self.calc_arg = calc_arg # needed for rewriting dptools command in job submission script
    
    def set_model(self, model_label):
        # NOTE: NEED TO SET THE LABEL BEFORE CALLING get_dpfaults
        #  Also, I suppose it's not really get_dpfaults if it can load custom envs
        if model_label:
            set_custom_env(model_label)
        self.graph, self.type_map = get_dpfaults()

    def submit_jobs(self, directories):
        from dptools.hpc import SlurmJob
        hpc_info = get_dpfaults(key="sbatch")
        sbatch_comment = hpc_info.pop("SBATCH_COMMENT")

        commands = f"dptools run {self.calc_arg} {self.structures[0]}"
        jobs = SlurmJob(sbatch_comment,
                        commands=commands,
                        directories=directories,
                        file_name="dptools.run.sh",
                        **hpc_info
                        )
        jobs.submit()

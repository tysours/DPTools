import os
from ruamel.yaml import YAML
from ase.io import read
import numpy as np

from dptools.simulate import Simulations
from dptools.simulate.parameters import get_parameter_sets
from dptools.utils import read_type_map
from dptools.cli import BaseCLI
from dptools.env import get_dpfaults, set_custom_env


class CLI(BaseCLI):
    help_info = "Run simulation using trained DP model "\
            "(USE COMMAND 'dptools set path/to/graph.pb' first)"
    def add_args(self):
        self.parser.add_argument(
            "calculation",
            type=str,
            help="Type of calculation to run (spe, opt, cellopt, nvt-md, npt-md, or params.yaml)",
            #choices=[k for k in Simulations.keys()] + ["path/to/params.yaml"], # messier than help comment IMO
        )
        self.parser.add_argument(   
            "structure",
            nargs="+",    # TODO: Add support for multiple structure inputs
            help="File containing structure to run calculation on (.traj, .xyz, .cif, etc.)"
        )
        self.parser.add_argument("-m", "--model-label", type=str, default=None,
                help="Label of specific model to use (see dptools set -h)")
        self.parser.add_argument("-s", "--submit", action="store_true",
                help="Automatically submit job(s) to train model(s) once input has been created")
        self.parser.add_argument("-g", "--generate-input", action="store_true",
                help="Only setup calculation and generate input files but do not run calculation")
        #self.parser.add_argument("-p", "--path", nargs=1, type=str, default="./",
        #        help="Specify path to write simulation files and results to")
        self.parser.add_argument("-o", "--output", type=str, default="{calculation}.traj",
                help="Name of file to write calculation output to")

    def main(self, args):
        self.set_model(args.model_label)
        self.set_params(args.calculation)
        self.set_structures(args.structure)
        if args.output == "{calculation}.traj": # replace default placeholder name
            args.output = f"{self.calc_type}.traj" 
        self.file_out = args.output

        if args.submit:
            self.submit_jobs()
        elif args.generate_input:
            raise NotImplementedError("--generate-input work in progress, harass me if you need it")
        else:
            self.run()

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
        self._label = model_label # need for submit_jobs()

    def set_structures(self, structures):
        index = -1
        self.structures = [os.path.abspath(s) for s in structures]
        if len(structures) == 1:
            dirs = ["."]
            if self.calc_type == "spe":
                index = ":"
        else:
            dirs = [os.path.dirname(s) for s in self.structures]
            if len(np.unique(dirs)) != len(self.structures):
                raise Exception("Can't resolve inputs, harass me to fix this")

        self.atoms = [read(s, index=index) for s in self.structures]
        self.dirs = dirs

    def submit_jobs(self):
        from dptools.hpc import SlurmJob
        hpc_info = get_dpfaults(key="sbatch")
        sbatch_comment = hpc_info.pop("SBATCH_COMMENT")

        f_arg = f"-o {self.file_out}"
        m_arg = f"-m {self._label} " if self._label else ""
        commands = f"dptools run {m_arg}{f_arg} {self.calc_arg} {self.structures[0]}"
        jobs = SlurmJob(sbatch_comment,
                        commands=commands,
                        directories=self.dirs,
                        file_name="dptools.run.sh",
                        **hpc_info
                        )
        jobs.submit()

    def run(self):
        wd = os.getcwd()
        for atoms, d in zip(self.atoms, self.dirs):
            os.chdir(d)
            sim = Simulations[self.calc_type](
                    atoms, 
                    self.graph,
                    type_map=read_type_map(self.type_map),
                    file_out=self.file_out,
                    path=".",
                    **self.params
                    )

            sim.run()
            os.chdir(wd)

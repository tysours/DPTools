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
    """
    Run LAMMPS simulations using trained DP models.

    :doc:`Complete documentation here<../commands/run>`

    Examples:

    .. code-block:: console

        $ dptools run opt start.traj # simple atomic position optimization
        $ dptools run cellopt start.traj # simple unit cell optimization
        $ dptools run /path/to/params.yaml start.traj # custom param file simulation
        $ dptools run -s eos 0*/start.traj # submit slurm job eos simulations on multiple structures
        $ dptools run -s -m water nvt-md start.traj # submit slurm nvt-md run using set water model
    """
    help_info = "Run simulation using trained DP model "\
            "(USE COMMAND 'dptools set path/to/graph.pb' first)"

    def add_args(self):
        self.parser.add_argument(
            "calculation",
            type=str,
            help="Type of calculation to run "\
                    "(spe, opt, cellopt, nvt-md, npt-md, eos, vib, or params.yaml)",
        )
        self.parser.add_argument(
            "structure",
            nargs="+",
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
            self.submit_jobs(sub=True)
        elif args.generate_input:
            self.submit_jobs(sub=False)
        else:
            self.run()

    def set_params(self, calc_arg):
        """
        Set simulation parameters either from simulation keyword or params.yaml file.

        Note:
            If using parameter file, you must at least retain the .yaml extension.

        Args:
            calc_arg (str): simulation keyword (e.g. `opt`) or path to params.yaml file.
        """

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
        """
        Load specific model (if model_label is not None) and set corresponding graph and type_map.

        Args:
            model_label (str or None): Label of specific model environment to load.
        """
        # NOTE: NEED TO SET THE LABEL BEFORE CALLING get_dpfaults
        #  Also, I suppose it's not really get_dpfaults if it can load custom envs
        if model_label:
            if os.path.isfile(model_label) and model_label.endswith(".pb"):
                err = "\nCan not load .pb files for 'dptools run -m ...' (long story)"\
                      ". Give model a label and use with set command! Example:\n\n\t"\
                      f"dptools set -m label {model_label}\n"
                raise ValueError(err)

            set_custom_env(model_label)

        self.graph, self.type_map = get_dpfaults()
        self._label = model_label # need for submit_jobs()

    def set_structures(self, structures):
        """
        Read and set structure inputs as ase.Atoms objects and set corresponding dirs.
        Only reads last index unless calc_type == spe, in which case single points are ran
        on all images of structure file.

        Args:
            structures (list of str): Paths to structure inputs to run simulations
                on (.traj, .xyz, .cif, etc.).
        """

        index = -1
        self.structures = [os.path.abspath(s) for s in structures]
        if len(structures) == 1:
            dirs = ["."]
            if self.calc_type == "spe":
                index = ":"
        else:
            dirs = [os.path.dirname(s) for s in self.structures]
            if len(np.unique(dirs)) != len(self.structures):
                # FIXME: Results are overwritten if multiple structure inputs are in the same dir
                raise Exception("Can't resolve inputs, harass me to fix this")

        self.atoms = [read(s, index=index) for s in self.structures]
        self.dirs = dirs

    def submit_jobs(self, sub=True):
        """
        Setup and (optionally) submit slurm jobs on all structure inputs.

        Args:
            sub (bool, optional): Submits slurm jobs if True, else only writes
                input files without submitting.
        """
        from dptools.hpc import SlurmJob
        hpc_info = get_dpfaults(key="sbatch")
        sbatch_comment = hpc_info.pop("SBATCH_COMMENT")

        f_arg = f"-o {self.file_out}"
        m_arg = f"-m {self._label} " if self._label else ""
        comm_base = f"dptools run {m_arg}{f_arg} {self.calc_arg} "
        commands = [comm_base + os.path.basename(s) for s in self.structures]
        jobs = SlurmJob(sbatch_comment,
                        commands=commands,
                        directories=self.dirs,
                        file_name="dptools.run.sh",
                        zip_commands=True,
                        **hpc_info
                        )
        jobs.write(sub=sub)

    def run(self):
        """
        Sequentially setup and run simulations on all structure inputs.
        """
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

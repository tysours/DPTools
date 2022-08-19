import os
import json

from dptools.cli import BaseCLI
from dptools.train import DeepInputs
from dptools.utils import randomize_seed
from dptools.hpc import SlurmJob


class CLI(BaseCLI):
    help_info = "Setup and submit jobs to train deepmd-kit models"
    def add_args(self):
        self.parser.add_argument("-e", "--ensemble", action="store_true",
                help="Make ensemble (4) of DP models to train")
        self.parser.add_argument("-s", "--submit", action="store_true",
                help="Automatically submit slurm job(s) to train model(s)")
        self.parser.add_argument("-p", "--path", type=str, default=".",
                help="Specify path to training directory")

    def main(self, args):
        self.path = os.path.abspath(args.path)
        if args.ensemble:
            self.make_ensemble() # sets self.dirs
        else:
            self.dirs = [path]
        self._sub = args.submit
        self.submit_jobs()

    def make_ensemble(self):
        with open("in.json") as file:
            in_json = json.loads(file.read())
        ens_dirs = ["00", "01", "02", "03"]
        self.dirs = [os.path.join(self.path, d) for d in ens_dirs]
        for d in self.dirs:
            jsn = randomize_seed(in_json)
            self.write_json(jsn, d)

    @staticmethod
    def write_json(src, dest):
        os.makedirs(dest, exist_ok=True)
        file_path = os.path.join(dest, "in.json")
        with open(file_path, "w") as file:
            file.write(json.dumps(src, indent=4))

    def submit_jobs(self):
        from dptools.env import get_dpfaults
        hpc_info = get_dpfaults(key="sbatch")
        sbatch_comment = hpc_info.pop("SBATCH_COMMENT")
        commands = ["dp train in.json", "dp freeze -o graph.pb"]
        jobs = SlurmJob(sbatch_comment,
                        commands=commands,
                        directories=self.dirs,
                        file_name="dptools.train.sh",
                        **hpc_info)
        jobs.write(sub=self._sub)

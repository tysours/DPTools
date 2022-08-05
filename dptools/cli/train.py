import os
import json

from dptools.cli import BaseCLI
from dptools.train import DeepInputs
from dptools.utils import randomize_seed
from dptools.hpc import SlurmJob


class CLI(BaseCLI):
    help_info = "Set up deepmd-kit training input from ASE .db files and train model"
    def add_args(self):
        self.parser.add_argument("dbs", nargs='+', metavar="db", help="ASE .db files")
        self.parser.add_argument("-e", "--ensemble", action="store_true",
                help="Make ensemble (4) of DP models to train")
        self.parser.add_argument("-s", "--submit", action="store_true",
                help="Automatically submit job(s) to train model(s) once input has been created")
        self.parser.add_argument("-n", nargs=1, type=int,
                help="Max number of images to take from each db")
        self.parser.add_argument("-p", "--path", nargs=1, type=str, default="./data",
                help="Specify path to dataset directory")

    def main(self, args):
        if args.n:
            raise NotImplementedError("n needs to be reworked, sorry (harass me if you need it)")
        sys_names = [db.split("/")[-1].split(".db")[0] for db in args.dbs]
        path = os.path.abspath(args.path)
        thing = DeepInputs(args.dbs, system_names=sys_names, path=path)
        self.ensemble = args.ensemble
        if self.ensemble:
            self.make_ensemble() # sets self.dirs
        else:
            self.dirs = ["."]
        if args.submit:
            self.submit_jobs()

    def make_ensemble(self):
        with open("in.json") as file:
            in_json = json.loads(file.read())
        self.dirs = ["00", "01", "02", "03"]
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
        jobs.submit()

import os
import glob
import json

from dptools.cli import BaseCLI
from dptools.utils import randomize_seed
from dptools.hpc import SlurmJob


class CLI(BaseCLI):
    """
    Setup and submit jobs to train single or ensemble of deepmd-kit models.

    Complete documentation: https://dptools.rtfd.io/en/latest/commands/train.html

    Examples:
        dptools train /path/to/dataset # simple single model
        dptools train -e /path/to/dataset # ensemble (4) of models
        dptools train -e -s /path/to/dataset # submit 4 slurm jobs to train ensemble
        dptools train -p /path/to/training/dir /path/to/dataset # specify dir to train in
        dptools train -i /path/to/in.json /path/to/dataset # specify in.json parameter file
    """

    help_info = "Setup and submit jobs to train deepmd-kit models"

    def add_args(self):
        self.parser.add_argument("dataset", type=str,
                help="Path to dataset parent directory")
        self.parser.add_argument("-e", "--ensemble", action="store_true",
                help="Make ensemble (4) of DP models to train")
        self.parser.add_argument("-s", "--submit", action="store_true",
                help="Automatically submit slurm job(s) to train model(s)")
        self.parser.add_argument("-p", "--path", type=str, default=".",
                help="Specify path to training directory")
        self.parser.add_argument("-i", "--input", type=str, default=None,
                help="Specify path to in.json deepmd parameter file to use for training")

    def main(self, args):
        if args.dataset == ".":
            raise ValueError("Do not train inside the dataset folder"\
                    " (dataset can not be '.')")
        self.datapath = os.path.abspath(args.dataset)
        self.path = os.path.abspath(args.path)
        if args.input:
            self._json = os.path.abspath(args.input)
        else:
            default = os.path.dirname(os.path.abspath(__file__))
            self._json = os.path.join(default, "../train/in.json")

        if args.ensemble:
            ens_dirs = ["00", "01", "02", "03"]
            self.dirs = [os.path.join(self.path, d) for d in ens_dirs]
        else:
            self.dirs = [self.path]
        self._sub = args.submit
        self.setup()
        self.submit_jobs()

    def setup(self):
        with open(self._json, "r") as file:
            in_json = json.loads(file.read())
        for d in self.dirs:
            jsn = randomize_seed(in_json)
            jsn = self.link_dirs(jsn)
            jsn = self.set_types(jsn)
            self.write_json(jsn, d)

    @staticmethod
    def write_json(src, dest):
        os.makedirs(dest, exist_ok=True)
        file_path = os.path.join(dest, "in.json")
        with open(file_path, "w") as file:
            file.write(json.dumps(src, indent=4))

    def link_dirs(self, in_json):
        possible_dirs = sorted(glob.glob(f"{self.datapath}/*"))
        dirs = [d for d in possible_dirs if self._check_dir(d)]
        train = [os.path.join(d, "train") for d in dirs]
        validation = [os.path.join(d, "validation") for d in dirs]
        in_json["training"]["training_data"]["systems"] = train
        in_json["training"]["validation_data"]["systems"] = validation
        return in_json

    def set_types(self, in_json):
        if not hasattr(self, "types"): # only need to read type_map once
            type_map_path = os.path.join(self.datapath, "type_map.json")
            with open(type_map_path, "r") as file:
                type_map = json.loads(file.read())
            self.types = [type_map[str(i)] for i in range(len(type_map))]

        in_json["model"]["type_map"] = self.types
        return in_json

    @staticmethod
    def _check_dir(d):
        if not os.path.isdir(d):
            return False
        check1 = "train" in os.listdir(d)
        check2 = "validation" in os.listdir(d)
        return check1 and check2

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

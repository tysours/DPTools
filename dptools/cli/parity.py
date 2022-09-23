import os
import json

from dptools.cli import BaseCLI
from dptools.train.parity import EvaluateDP

class CLI(BaseCLI):
    """
    Generate parity plots comparing DP model accuracy for energy and force
    (and stress if available) predictions with ab-initio values.

    :doc:`Complete documentation here<../commands/parity>`

    Examples:

    .. code-block:: console

        $ dptools parity
        $ dptools parity /path/to/dataset/system*/test/set*
        $ dptools parity -m ../old_graph.pb test_set.traj
        $ dptools parity -l mae
    """
    help_info = "Generate energy and force (and stress if available) prediction parity plots for DP model"
    def add_args(self):
        # TODO: add more optional args (e.g. save plot)
        self.parser.add_argument("systems", nargs="*", metavar="system", help="Paths to deepmd-kit dataset folders, .traj, .db, etc.")
        self.parser.add_argument("-m", "--model", type=str, default="./graph.pb",
                help="Specify path of frozen .pb deepmd model to use")
        self.parser.add_argument("-l", "--loss-function", type=str, default="mse", choices=["mse", "mae", "rmse"],
                help="Type of loss function to display for parity plot error")
        self.parser.add_argument("--xyz", action="store_true",
                help="Plot each xyz force component separately")
        self.parser.add_argument("--fancy", action="store_true",
                help="Create fancy density heat map for forces parity plot")

    def main(self, args):
        if len(args.systems) > 0:
            systems = args.systems
        else:
            systems = self.read_systems()
        if args.fancy:
            raise NotImplementedError("Fancy plots coming soon...")
        if args.xyz:
            raise NotImplementedError("Separate xyz components plots coming soon...")
        evaldpmd = EvaluateDeepMD(systems, dp_graph=args.model)
        evaldpmd.plot(loss=args.loss_function)

    @staticmethod
    def read_systems():
        """
        Load test sets from system paths in in.json training parameter file.

        Returns:
            list of str: Paths to system test sets found in training json file.
        """

        if "out.json" not in os.listdir() and "in.json" not in os.listdir():
            raise FileNotFoundError("Systems not specified and no in.json in $PWD")
        in_file = "in.json" if "in.json" in os.listdir() else "out.json"
        with open("in.json") as file:
            params = json.loads(file.read())
        systems = params["training"]["training_data"]["systems"]
        return [f"{s.split('/train')[0]}/test/set.000" for s in systems]

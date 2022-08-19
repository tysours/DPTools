import os

from dptools.cli import BaseCLI
from dptools.train import DeepInputs


class CLI(BaseCLI):
    help_info = "Set up deepmd-kit training input from ASE .db files"
    def add_args(self):
        self.parser.add_argument("dbs", nargs='+', metavar="db", help="ASE .db files")
        self.parser.add_argument("-n", nargs=1, type=int,
                help="Max number of images to take from each db")
        self.parser.add_argument("-p", "--path", type=str, default="./data",
                help="Specify path to dataset directory")

    def main(self, args):
        if args.n:
            raise NotImplementedError("n needs to be reworked, sorry (harass me if you need it)")
        sys_names = [self.get_name(db) for db in args.dbs]
        path = os.path.abspath(args.path)
        thing = DeepInputs(args.dbs, system_names=sys_names, path=path)

    @staticmethod
    def get_name(db):
        return os.path.basename(db).split(".db")[0]

from dptools.cli import BaseCLI
from dptools.parity import EvaluateDeepMD

class CLI(BaseCLI):
    def add_args(self):
        # TODO: add more optional args (e.g. save plot)
        self.parser.add_argument("systems", nargs="*", metavar="system", help="Paths to deepmd-kit dataset folders, .traj, .db, etc.")
        self.parser.add_argument("-m", "--model", type=str, default="./graph.pb",
                help="Specify path of frozen .pb deepmd model to use")
        self.parser.add_argument("-l", "--loss-function", type=str, default="mse", choices=["mse", "mae", "rmse"],
                help="Type of loss function to display for parity plot error")

    def main(self, args):
        print(args)
        if len(args.systems) > 0:
            systems = args.systems
        else:
            systems = self.read_systems()
        evaldpmd = EvaluateDeepMD(systems, dp_graph=args.model)
        evaldpmd.plot(loss=args.loss_function)


    @staticmethod
    def read_systems():
        if "in.json" not in os.listdir():
            raise FileNotFoundError("Systems not specified and no in.json in $PWD")
        with open("in.json") as file:
            params = json.loads(file.read())
        systems = params["training"]['training_data']['systems']
        return [f"{s.split('/train')[0]}/test/set.000" for s in systems]

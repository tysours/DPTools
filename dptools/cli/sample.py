from ase.io import read, write
import numpy as np
import os

from dptools.train.ensemble import SampleConfigs
from dptools.cli import BaseCLI
from dptools.utils import graph2typemap, read_type_map

class CLI(BaseCLI):
    help_info = "Select new training configs from MD traj "\
        "using force prediction deviations from ensemble of DPs"
    def add_args(self):
        help="Snapshots from MD simulation to select new training configuraitons from (.traj or similar)"
        self.parser.add_argument(
            "configurations",
            nargs="+",
            help=help
        )
        self.parser.add_argument("-m", "--model-ensemble", nargs="+", type=str,
                help="Paths to ensemble of models or label of set models")
        self.parser.add_argument("-n", type=int, default=300,
                help="Max number of new configurations to select")
        self.parser.add_argument("--lo", type=float, default=0.05,
                help="Min value of eps_t (force dev) to select new configs from")
        self.parser.add_argument("--hi", type=float, default=0.35,
                help="Max value of eps_t (force dev) to select new configs from")
        self.parser.add_argument("-o", "--output", nargs=1, type=str, default="new_configs.traj",
                help="File to write new configurations to")
        self.parser.add_argument("-p", "--plot-dev", action="store_true",
                help="Plot max force deviation of model ensemble for each config")


    def main(self, args):
        self.outfile = os.path.basename(args.output)
        self.load_ensemble(args.model_ensemble) # sets self.type_map and self.graphs
        self.set_configs(args.configurations)
        self.devs = [] # max force deviation of model ensemble

        wd = os.getcwd()
        for configs, dir in zip(self.configs, self.dirs):
            os.chdir(dir)

            self.sample(configs, args)

            os.chdir(wd)

        if args.plot_dev:
            self.plot()

    def load_ensemble(self, ensemble):
        if not ensemble or len(ensemble) == 1:
            from dptools.env import set_custom_env, get_dpfaults
            if ensemble is not None and len(ensemble) == 1:
                set_custom_env(ensemble[0])
            defaults = get_dpfaults(key="ensemble")
            self.type_map, *ensemble = defaults
        else:
            self.type_map = graph2typemap(ensemble[0])
        self.ensemble = ensemble

    def set_configs(self, configs):
        self.configs = [os.path.abspath(c) for c in configs]
        if len(configs) == 1:
            dirs = ["."]
        else:
            dirs = [os.path.dirname(c) for c in self.configs]
            if len(np.unique(dirs)) != len(self.configs):
                # FIXME: Results are overwritten if multiple structure inputs are in the same dir
                raise Exception("Can't resolve inputs, harass me to fix this")
        self.dirs = dirs
    
    def sample(self, configs, args):
        self.sampler = SampleConfigs(configs, self.ensemble, read_type_map(self.type_map))
        new_configs = self.sampler.sample(lo=args.lo, hi=args.hi, n=args.n)

        self.devs.append(self.sampler.dev)
        write(self.outfile, new_configs)

    def plot(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5.5, 4))
        for dev, dir in zip(self.devs, self.dirs):
            ax = self.sampler.plot(dev=dev, ax=ax, label=os.path.relpath(dir))
        ax.legend()
        plt.show()

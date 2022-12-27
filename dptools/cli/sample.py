import os
import numpy as np
from ase.io import write

from dptools.train.ensemble import SampleConfigs
from dptools.cli import BaseCLI
from dptools.utils import graph2typemap, read_type_map
from dptools.env import load, get_dpfaults

class CLI(BaseCLI):
    """
    Intelligently select new training configurations using an ensemble of models
    and the approach described in DP-GEN (DOI: 10.1016/j.cpc.2020.107206).

    :doc:`Complete documentation here<../commands/sample>`

    Examples:

    .. code-block:: console

        $ dptools sample -n 200 nvt-md.traj
        $ dptools sample -n 100 --lo 0.05 --hi 0.25 nvt-md.traj
        $ dptools sample -m water_ensemble -p npt-md.traj

    """
    help_info = "Select new training configs from MD traj "\
        "using force prediction deviations from ensemble of DPs"

    def add_args(self):
        self.parser.add_argument(
            "configurations",
            nargs="+",
            help="Snapshots from MD simulation to select new training configuraitons "\
                "from (.traj or similar)"
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
                help="Plot histogram of max force deviation of model ensemble for each config")
        self.parser.add_argument("--plot-steps", action="store_true",
                help="Plot dev versus number of steps")


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

        if args.plot_dev or args.plot_steps:
            self.plot(steps=args.plot_steps)

    def load_ensemble(self, ensemble):
        if not ensemble or len(ensemble) == 1:
            if ensemble is not None and len(ensemble) == 1:
                load(ensemble[0])
            defaults = get_dpfaults(key="ensemble")
            #self.type_map, *ensemble = defaults
            *ensemble, self.type_map = defaults
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

    def plot(self, steps=False):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(5.5, 4))
        for dev, _dir in zip(self.devs, self.dirs):
            ax = self.sampler.plot(dev=dev, steps=steps, ax=ax, label=os.path.relpath(_dir))
        if len(self.dirs) > 1:
            ax.legend()
        plt.show()

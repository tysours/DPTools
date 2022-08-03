from ase.io import read, write
import numpy as np
import random
import os

from dptools.utils import graph2typemap, read_type_map
from dptools.cli import BaseCLI

class SampleConfigs:
    def __init__(self, configs, graphs, type_map=None, indices=":"):
        if isinstance(configs, str):
            self.configs = read(configs, index=indices)
        else:
            self.configs = configs
        if not type_map:
            type_map = graph2typemap(graphs[0])
        self.type_map = type_map
        self.graphs = graphs

    def get_dev(self):
        from deepmd.infer import calc_model_devi
        from deepmd.infer import DeepPot as DP
        pos = np.array([a.get_positions().flatten() for a in self.configs])
        cell = np.array([a.cell.array.flatten() for a in self.configs])
        types = [self.type_map[a.symbol] for a in self.configs[0]]

        models = [DP(g) for g in self.graphs]

        dev = calc_model_devi(pos, cell, types, models, nopbc=False)[:, 4]
        return dev

    def sample(self, lo=0.05, hi=0.35, n=300):
        dev = self.get_dev()
        i_configs = np.where(np.logical_and(dev>=lo, dev<=hi))[0]
        n_sample = n if n < len(i_configs) else len(i_configs)
        i_new_configs = random.sample(list(i_configs), n_sample)
        new_configs = [self.configs[i] for i in i_new_configs]
        return new_configs


class CLI(BaseCLI):
    def add_args(self):
        help="Snapshots from MD simulation to select new training configuraitons from (.traj or similar)"
        self.parser.add_argument(
            "configurations",
            help=help
        )
        self.parser.add_argument("-n", type=int, default=300,
                help="Max number of new configurations to select")
        self.parser.add_argument("--lo", type=float, default=0.05,
                help="Min value of eps_t (force dev) to select new configs from")
        self.parser.add_argument("--hi", type=float, default=0.35,
                help="Max value of eps_t (force dev) to select new configs from")
        self.parser.add_argument("-o", "--output", nargs=1, type=str, default="new_configs.traj",
                help="File to write new configurations to")
        self.parser.add_argument("-m", "--model-ensemble", nargs="+", type=str,
                help="Paths to ensemble of models or label of set models")


    def main(self, args):
        configs = read(args.configurations, index=":")
        outfile = os.path.abspath(args.output)
        self.load_ensemble(args.model_ensemble) # sets self.type_map and self.graphs

        sampler = SampleConfigs(configs, self.ensemble, read_type_map(self.type_map))
        new_configs = sampler.sample(lo=args.lo, hi=args.hi, n=args.n)
        write(outfile, new_configs)

    def load_ensemble(self, ensemble):
        if not ensemble:
            from dptools.env import get_dpfaults
            defaults = get_dpfaults(key="ensemble")
            self.type_map, *ensemble = defaults
        elif len(ensemble) == 1:
            raise NotImplementedError("ensemble label not implemented, harass me if you need it")
        else:
            self.type_map = graph2typemap(ensemble[0])
        self.ensemble = ensemble

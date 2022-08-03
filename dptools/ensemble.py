from ase.io import read
import numpy as np
import random

from dptools.utils import graph2typemap
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
        pos = np.array([a.get_positions().flatten() for a in self.configs])
        cell = np.array([a.cell.array.flatten() for a in self.configs])
        types = [self.type_map[a.symbol] for a in self.configs[0]]

        models = [DP(g) for g in self.graphs]

        dev = calc_model_devi(pos, cell, types, models, nopbc=False)[:, 4]
        return dev

    def sample(self, lo=0.05, hi=0.35, n=300):
        dev = self.get_dev()
        i_configs = np.where(np.logcal_and(dev>=lo, dev<=hi))
        n_sample = n if n < len(i_configs) else len(i_configs)
        i_new_configs = random.sample(i_configs, n_sample)
        new_configs = [self.configs[i] for i in i_new_configs]
        return new_configs


#def get_dev(atoms, graphs, type_map):


class CLI(BaseCLI):
    def add_args(self):
        help="Snapshots from MD simulation to select new training configuraitons from (.traj or similar)"
        self.parser.add_argument(
            "configurations",
            help=help
        )

    def main(self, args):
        raise NotImplementedError("Coming soon...")

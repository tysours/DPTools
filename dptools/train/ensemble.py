from ase.io import read, write
import numpy as np
import random
import os

from dptools.utils import graph2typemap, next_color

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
        self.dev = self.get_dev()
        i_configs = np.where(np.logical_and(self.dev>=lo, self.dev<=hi))[0]
        n_sample = n if n < len(i_configs) else len(i_configs)
        i_new_configs = random.sample(list(i_configs), n_sample)
        new_configs = [self.configs[i] for i in i_new_configs]
        return new_configs

    def plot(self, dev=None, ax=None, color=None, label=None):
        import matplotlib.pyplot as plt
        import seaborn as sns
        if dev is None:
            if hasattr(self, "dev"):
                dev = self.dev
            else:
                dev = self.get_dev()
        ax = plt.gca() if ax is None else ax
        color = next_color() if color is None else color
        
        sns.kdeplot(dev, fill=True, label=label or "")
        return ax

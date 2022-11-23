"""
Module for working with ensembles of DP models.
"""
from ase.io import read, write
import numpy as np
import random
import os

from dptools.utils import graph2typemap, next_color

class SampleConfigs:
    """
    Class for selecting new training configurations from snapshots of a molecular
    dynamnics trajectory (or some similar method). Uses an ensemble of models to
    calculate eps_t (max force prediction deviation), and then select new
    configurations within some specified tolerance such that new configurations
    belong to realistic but unexplored regions of configuration space.

    Follows the guidelines described by DP-GEN (full credit to the authors).
    For more details on eps_t and the methodologies used here, refer to:

        Y. Zhang, H. Wang, W. Chen, J. Zeng, L. Zhang, H. Wang and W. E,
        Comput. Phys. Commun., 2020, 253, 107206.

    Please cite the above reference if you use this script for training models in
    published work. Also, check out the DP-GEN GitHub for a robust, standalone package
    for automatically and efficiently training deepmd-kit MLPs.

    Args:
        configs (list[ase.Atoms] or str): List of atomic configurations from MD trajectory
            (or str to .traj, .xyz, etc. that contains configs) to sample from.
        graphs (list[str]): List of paths to ensemble of deepmd models (.pb files).
            e.g., ['00/graph.pb', '01/graph.pb', '02/graph.pb', '03/graph.pb']
        type_map (dict, optional): Dictionary mapping each atom type (symbol) to
            corresponding index. If None specified, infer from graph file.
        indices (str): Index slice to use for reading configs if str input supplied
            (used in command ase.io.read(config, index=indices)).
    """
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
        if "dev.npy" in os.listdir():
            old_dev = np.load("dev.npy")
            if len(old_dev) == len(self.configs): # only read dev if configs haven't changed
                print(f"Reading dev from {os.path.abspath('dev.npy')} ...")
                return old_dev

        from deepmd.infer import calc_model_devi
        from deepmd.infer import DeepPot as DP
        pos = np.array([a.get_positions().flatten() for a in self.configs])
        cell = np.array([a.cell.array.flatten() for a in self.configs])
        types = [self.type_map[a.symbol] for a in self.configs[0]]

        models = [DP(g) for g in self.graphs]

        dev = calc_model_devi(pos, cell, types, models, nopbc=False)[:, 4]
        np.save("dev.npy", dev)
        return dev

    def sample(self, lo=0.05, hi=0.35, n=300):
        """
        Select n new training configurations with lo < eps_t < hi.

        .. note::

            ``hi`` must be chosen carefully to allow for the selection of
            configurations that belong to underexplored regions of
            configuration space, but not set so high that nonsensical,
            unphysical configs are chosen.

        Args:
            lo (float): Lower bound eps_t tolerance for sampling.
            hi (float): Upper bound eps_t tolerance for sampling.
            n (int): Maximum number of configurations to select. If the number of
                configs within lo and hi is < n, then all configs between lo and hi
                are returned.

        Returns:
            new_configs (list[ase.Atoms]): Configurations with eps_t within the
                specified tolerance criteria.
        """
        if hi > 0.5:
            warn = """
               ----------------------------------------------------------------------------------
              | WARNING: High upper bound eps_t tolerance specified!                             |
              |----------------------------------------------------------------------------------|
              | Large eps_t might correspond with unphysical (bad) configurations.               |
              | IF YOU USE THESE CONFIGS FOR TRAINING, MAKE SURE YOUR DFT CALCULATION CONVERGES! |
              | You will regret this if you do not heed this warning, trust me.                  |
              |__________________________________________________________________________________|
               """ # large obnoxious warning box for emphasis
            print(warn)

        self.dev = self.get_dev()
        i_configs = np.where(np.logical_and(self.dev>=lo, self.dev<=hi))[0]
        n_sample = n if n < len(i_configs) else len(i_configs)
        i_new_configs = random.sample(list(i_configs), n_sample)
        new_configs = [self.configs[i] for i in sorted(i_new_configs)]
        return new_configs

    def plot(self, dev=None, steps=False, ax=None, color=None, label=None):
        """
        Create kernel density estimation plot (fancy smooth histogram) for
        all eps_t values in configs input.

        Requires seaborn python package to be installed!
        https://seaborn.pydata.org

        Args:
            dev (array-like): Optional list of dev values to plot, calculate if None given.
            steps (bool): If False, plot histogram of dev values. If True, plot dev versus
                step number (divided by write_freq).
            ax (Axes): Specific mpl Axes to plot on.
            color (str): Color to use for plot.
            label (str): Label to use for legend entry.
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        if dev is None:
            if hasattr(self, "dev"):
                dev = self.dev
            else:
                dev = self.get_dev()
        ax = plt.gca() if ax is None else ax
        color = next_color() if color is None else color

        if steps:
            ax.set_xlabel("Steps / write_freq", fontsize=14)
            ax.set_ylabel("$\epsilon_t$ (eV/Å)", fontsize=14)
            plt.plot(np.arange(len(dev)), dev, '-', color=color, label=label or "")
        else:
            sns.kdeplot(dev, fill=True, color=color, label=label or "")
            ax.set_ylabel("Density", fontsize=14)
            ax.set_xlabel("$\epsilon_t$ (eV/Å)", fontsize=14)
        ax.locator_params('both', nbins=5)
        ax.tick_params(labelsize=12)
        plt.tight_layout()
        return ax

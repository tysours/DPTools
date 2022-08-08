from ase.io import read
from ase.db import connect
import numpy as np
import matplotlib.pyplot as plt
import os
import json

#seaborn.color_palette('deep')
colors = [(0.2980392156862745, 0.4470588235294118, 0.6901960784313725),
          (0.8666666666666667, 0.5176470588235295, 0.3215686274509804),
          (0.3333333333333333, 0.6588235294117647, 0.40784313725490196),
          (0.7686274509803922, 0.3058823529411765, 0.3215686274509804),
          (0.5058823529411764, 0.4470588235294118, 0.7019607843137254),
          (0.5764705882352941, 0.47058823529411764, 0.3764705882352941),
          (0.8549019607843137, 0.5450980392156862, 0.7647058823529411),
          (0.5490196078431373, 0.5490196078431373, 0.5490196078431373),
          (0.8, 0.7254901960784313, 0.4549019607843137),
          (0.39215686274509803, 0.7098039215686275, 0.803921568627451)]

class EvaluateDeepMD:
    def __init__(self, test_sets, dp_graph='graph.pb', save_plot=False):
        from deepmd.infer import DeepPot as DP
        self.dp = DP(dp_graph)
        if isinstance(test_sets, str):
            test_sets = [test_sets]

        self.energies = []
        self.forces = []
        self.virials = []
        self.sets = test_sets
        for test_set in self.sets:
            energies, forces, virials = self.evaluate(test_set)
            self.energies.append(energies)
            self.forces.append(forces)
            if virials is not None:
                self.virials.append(virials)

        self.set_mse()
        self.save = save_plot

    def set_mse(self):
        self.all_mse = [[self.get_mse(e), self.get_mse(f)]
                         for e, f in zip(self.energies, self.forces)]
        if len(self.virials) > 0:
            self.all_v_mse = [self.get_mse(v) for v in self.virials]
            self.v_mse = self.get_mse(np.vstack(self.virials))

        self.mse = [self.get_mse(np.vstack(self.energies)),
                    self.get_mse(np.vstack(self.forces))]

    def evaluate(self, test_set):
        coord = np.load(f'{test_set}/coord.npy')
        cell = np.load(f'{test_set}/box.npy')
        atype = np.loadtxt(f'{test_set}/../type.raw', dtype=int)
        e, f, v = self.dp.eval(coord, cell, atype)
        e = e.flatten()
        f = f.flatten()
        v = v.flatten()

        real_e = np.load(f'{test_set}/energy.npy')
        real_f = np.load(f'{test_set}/force.npy').flatten()
        if 'virial.npy' in os.listdir(test_set):
            real_v = np.load(f'{test_set}/virial.npy').flatten()
            virials = np.append(real_v[:, np.newaxis], v[:, np.newaxis], axis=1)
        else:
            virials = None

        energies = np.append(real_e[:, np.newaxis], e[:, np.newaxis], axis=1)
        forces = np.append(real_f[:, np.newaxis], f[:, np.newaxis], axis=1)
        return energies, forces, virials

    @staticmethod
    def get_mse(data):
        return np.mean((data[:, 0] - data[:, 1])**2)

    @staticmethod
    def get_rmse(data):
        return np.sqrt(np.mean((data[:, 0] - data[:, 1])**2))

    @staticmethod
    def get_mae(data):
        return np.mean(np.abs(data[:, 0] - data[:, 1]))

    @staticmethod
    def plot_yx(dft, ax):
        xrng = max(dft) - min(dft)
        xmin = min(dft) - 0.05 * xrng
        xmax = max(dft) + 0.05 * xrng
        ax.plot([xmin, xmax], [xmin, xmax], '--k', zorder=1)
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([xmin, xmax])
        return

    def plot_parity(self, data, label, color, loss="mse", ax=None):
        if ax is None:
            ax = plt.gca()
        err = getattr(self, f"get_{loss.lower()}")(data)
        ax.plot(data[:, 0], data[:, 1], "o", ms=3, color=color, alpha=0.20)
        ax.annotate(f"{loss.upper()} = {err:.3e}", xy=(0.1, 0.85), xycoords="axes fraction", fontsize=12)
        self.plot_yx(data[:, 0], ax)
        ax.set_ylabel(f"DP {label}", fontsize=14)
        ax.set_xlabel(f"DFT {label}", fontsize=14)
        ax.tick_params(labelsize=12)

    def plot(self, loss="mse", axs=None):
        if axs is None:
            if len(self.virials) > 0:
                fig, axs = plt.subplots(1, 3, figsize=(12.75, 3.5))
                v_data = np.vstack(self.virials)
            else:
                fig, axs = plt.subplots(1, 2, figsize=(8.5, 3.5))

        # TODO: Add ability to plot inidividual test sets
        #np.save('energies', np.array(self.energies))
        #np.save('forces', np.array(self.forces))
        e_data = np.vstack(self.energies)
        f_data = np.vstack(self.forces)

        self.plot_parity(e_data, "Energy (eV)", colors[3], loss=loss, ax=axs[0])
        self.plot_parity(f_data, "Force (eV/Å)", colors[0], loss=loss, ax=axs[1])
        if len(axs) == 3:
            self.plot_parity(v_data, "Virial", colors[2], loss=loss, ax=axs[2])
        plt.tight_layout()
        plt.subplots_adjust(wspace=0.3)
        if self.save:
            plt.savefig('results.png')
        else:
            plt.show()

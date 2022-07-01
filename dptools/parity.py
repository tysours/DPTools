#!/usr/bin/env python

from ase.io import read
from ase.db import connect
from deepmd.infer import DeepPot as DP
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

colors = sns.color_palette('deep')
class EvaluateDeepMD:
    def __init__(self, test_sets, dp_graph='graph.pb', save_plot=False):
        self.dp = DP(dp_graph)
        if isinstance(test_sets, str):
            test_sets = [test_sets]

        self.energies = []
        self.forces = []
        self.virials = []
        self.sets = test_sets
        #with open('sets', 'w') as file:
        #    for s in self.sets:
        #        file.write(f'{s}\n')
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
    def plot_yx(dft, ax):
        xrng = max(dft) - min(dft)
        xmin = min(dft) - 0.05 * xrng
        xmax = max(dft) + 0.05 * xrng
        ax.plot([xmin, xmax], [xmin, xmax], '--k', zorder=1)
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([xmin, xmax])
        return


    def plot(self, axs=None):
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

        axs[0].plot(e_data[:,0], e_data[:,1], 'o', ms=3, color=colors[3], alpha=0.25)
        axs[0].annotate(f"MSE = {self.mse[0]:.3e}", xy=(0.1, 0.85), xycoords='axes fraction', fontsize=12)
        self.plot_yx(e_data[:,0], axs[0])
        axs[0].set_ylabel('DP Energy (eV)', fontsize=14)
        axs[0].set_xlabel('DFT Energy (eV)', fontsize=14)
        axs[0].tick_params(labelsize=12)
        axs[1].plot(f_data[:,0], f_data[:,1], 'o', color=colors[0], ms=3, alpha=0.15)
        axs[1].annotate(f"MSE = {self.mse[1]:.3e}", xy=(0.1, 0.85), xycoords='axes fraction', fontsize=12)
        axs[1].set_ylabel('DP Force (eV/Å)', fontsize=14)
        axs[1].set_xlabel('DFT Force (eV/Å)', fontsize=14)
        axs[1].tick_params(labelsize=12)
        self.plot_yx(f_data[:,0], axs[1])
        if len(axs) == 3:
            axs[2].plot(v_data[:,0], v_data[:,1], 'o', ms=3, color=colors[2], alpha=0.2)
            axs[2].annotate(f"MSE = {self.v_mse:.3e}", xy=(0.1, 0.85), xycoords='axes fraction', fontsize=12)
            self.plot_yx(v_data[:,0], axs[2])
            axs[2].set_ylabel('DP Virial (virial units?)', fontsize=14)
            axs[2].set_xlabel('DFT Virial (virial units?)', fontsize=14)
            axs[2].tick_params(labelsize=12)
        plt.tight_layout()
        plt.subplots_adjust(wspace=0.3)
        if self.save:
            plt.savefig('results.png')
        else:
            plt.show()


class ShiftDP(EvaluateDeepMD):
    def __init__(self, test_sets, dp_graph='graph.pb', save_plot=False):
        from zeoml.cifs.data import opts
        super.__init__(test_sets, dp_graph=dp_graph, save_plot=save_plot)

    def evaluate(self, test_set):
        coord = np.load(f'{test_set}/coord.npy')
        cell = np.load(f'{test_set}/box.npy')
        atype = np.loadtxt(f'{test_set}/../type.raw', dtype=int)
        e, f, v = self.dp.eval(coord, cell, atype)
        opt_e = self.dp.eval(opts[code]['positions'], opts[code]['cell'], opts[code]['types'])
        print(opt_e)
        e = e.flatten() - opt_e
        f = f.flatten()
        v = v.flatten()

        code = test_set.split('/')[1]

        real_e = np.load(f'{test_set}/energy.npy')
        real_e -= opts[code]['energy']
        real_f = np.load(f'{test_set}/force.npy').flatten()
        if 'virial.npy' in os.listdir(test_set):
            real_v = np.load(f'{test_set}/virial.npy').flatten()
            virials = np.append(real_v[:, np.newaxis], v[:, np.newaxis], axis=1)
        else:
            virials = None

        energies = np.append(real_e[:, np.newaxis], e[:, np.newaxis], axis=1)
        forces = np.append(real_f[:, np.newaxis], f[:, np.newaxis], axis=1)
        return energies, forces, virials


if __name__ == '__main__':
    test_sets = 'data/test.set'
    save = False
    model_name = 'graph.pb'
    if len(sys.argv) > 1:
        test_sets = []
        for arg in sys.argv[1:]:
            if arg == '-s':
                save = True
            elif '-m' in arg:
                model_name = arg.split('=')[-1]
            else:
                test_sets.append(arg)

    if model_name not in os.listdir():
        os.system(f'dp freeze -o {model_name}')

    import time
    ti = time.time()
    thing = EvaluateDeepMD(test_sets, dp_graph=model_name, save_plot=save)
    print((time.time() - ti)/60, 'MINUTES')
    thing.plot()

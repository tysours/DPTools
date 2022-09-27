"""
Module to generate parity plots to compare DP model predictions with corresponding
*ab-initio* values.
"""
import numpy as np
import matplotlib.pyplot as plt
import os

from dptools.utils import colors


class EvaluateDP:
    """
    Class to read deepmd test sets (created with CLI :doc:`../commands/input` command
    or :class:`~dptools.train.DeepInput`) and create parity plots for DP predictions.

    Args:
        test_sets (list[str] or str): Paths to deepmd test set folders. E.g.,
            ``'data/system1/test/set.000'``
            # TODO: Add support for other input types (.traj with vasp calculators, etc.)

        dp_graph (str): Path to deepmd model to use for DP predictions.

        per_atom (bool): If True, normalize all energies per number of atoms. False uses
            raw energies for parity plot and loss function evaluations.

        save_plot (bool): Save parity plot to parity.png if True.
    """

    def __init__(self, test_sets, dp_graph="graph.pb", per_atom=False, save_plot=False):
        from deepmd.infer import DeepPot as DP
        self.dp = DP(dp_graph)
        if isinstance(test_sets, str):
            test_sets = [test_sets]

        self._per_atom = per_atom

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
        coord = np.load(f"{test_set}/coord.npy")
        cell = np.load(f"{test_set}/box.npy")
        atype = np.loadtxt(f"{test_set}/../type.raw", dtype=int)
        e_dp, f_dp, v_dp = self.dp.eval(coord, cell, atype)
        e_dp = e_dp.flatten()
        f_dp = f_dp.flatten()
        v_dp = v_dp.flatten()

        e_dft = np.load(f"{test_set}/energy.npy")
        f_dft = np.load(f"{test_set}/force.npy").flatten()
        if "virial.npy" in os.listdir(test_set):
            v_dft = np.load(f"{test_set}/virial.npy").flatten()
            virials = np.append(v_dft[:, np.newaxis], v_dp[:, np.newaxis], axis=1)
        else:
            virials = None

        energies = np.append(e_dft[:, np.newaxis], e_dp[:, np.newaxis], axis=1)
        if self._per_atom:
            n_atoms = len(atype)
            energies /= n_atoms
        forces = np.append(f_dft[:, np.newaxis], f_dp[:, np.newaxis], axis=1)
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
        ax.plot([xmin, xmax], [xmin, xmax], "--k", zorder=1)
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([xmin, xmax])

    def plot_parity(self, data, label, color, loss="mse", ax=None, fancy=False):
        if ax is None:
            ax = plt.gca()
        err = getattr(self, f"get_{loss.lower()}")(data)
        if not fancy:
            ax.plot(data[:, 0], data[:, 1], "o", ms=3, color=color, alpha=0.20)
        else:
            density_scatter(data[:, 0], data[:, 1], ax=ax, zorder=10)
        self.plot_yx(data[:, 0], ax)
        ax.annotate(f"{loss.upper()} = {err:.3e}", xy=(0.1, 0.85),
                xycoords="axes fraction", fontsize=12)
        ax.set_ylabel(f"DP {label}", fontsize=14)
        ax.set_xlabel(f"DFT {label}", fontsize=14)
        ax.tick_params(labelsize=12)

    def plot(self, loss="mse", axs=None, xyz=False, fancy=False):
        """
        Plot energy, force, and virial (if available) parity plots for DP predictions.

        Args:
            loss (str): {mse,mae,rmse} type of loss/error function to use for parity plot
                error annotation.
            axs (list[matplotlib.pyplot.Axes]): Optional, specific axes objects to plot on.
            xyz (bool): If True, plot all xyz force components in separate parity plots. False
                plots all components together (recommended, usually pointless to separate).
            fancy (bool): If True, create fancy density parity plot for force predictions.
        """
        n_plots = 2
        if axs is None:
            if len(self.virials) > 0:
                n_plots += 1
                v_data = np.vstack(self.virials)
            if xyz:
                n_plots += 2
        width = 0.5 + 4 * n_plots
        fig, axs = plt.subplots(1, n_plots, figsize=(width, 3.5))

        # TODO: Add ability to plot inidividual test sets
        #np.save("energies", np.array(self.energies))
        #np.save("forces", np.array(self.forces))
        e_data = np.vstack(self.energies)
        f_data = np.vstack(self.forces)

        e_units = "eV" if not self._per_atom else "eV/atom"
        self.plot_parity(e_data, f"Energy ({e_units})", colors[3], loss=loss, ax=axs[0])
        if not xyz:
            self.plot_parity(f_data, "Force (eV/Å)", colors[0], loss=loss, ax=axs[1], fancy=fancy)
        else:
            self.plot_parity(f_data[::3, :], "F$_x$ (eV/Å)", colors[0],
                    loss=loss, ax=axs[1], fancy=fancy)

            self.plot_parity(f_data[1::3, :], "F$_y$ (eV/Å)", colors[0],
                    loss=loss, ax=axs[2], fancy=fancy)

            self.plot_parity(f_data[2::3, :], "F$_z$ (eV/Å)", colors[0],
                    loss=loss, ax=axs[3], fancy=fancy)

        if len(axs) in [3, 5]:
            self.plot_parity(v_data, "Virial", colors[2], loss=loss, ax=axs[-1])
        plt.tight_layout()
        plt.subplots_adjust(wspace=0.3)
        if self.save:
            plt.savefig("parity.png")
        else:
            plt.show()


def density_scatter(x, y, ax=None, bins=300, **kwargs):
    """
    Plot fancy density parity plot. Requires scipy package!

    Args:
        x (array-like): x-axis values to plot.
        y (array-like): y-axis values to plot.
        ax (matplotlib.axes.Axes): Axes object to plot on.
        bins (int): Number of bins to partition off x y values into. Passed to
            np.histogram2d(bins=bins).
        **kwargs: Any additional keyword-args for matplotlib.pyplot.scatter().
    """
    from scipy.interpolate import interpn
    if ax is None:
        fig, ax = plt.subplots()

    data, x_e, y_e = np.histogram2d(x, y, bins=bins, density=True)

    z = interpn((0.5 * (x_e[1:] + x_e[:-1]), 0.5 * (y_e[1:] + y_e[:-1])),
                data,
                np.vstack([x,y]).T,
                method="splinef2d",
                bounds_error=False)

    z[np.where(np.isnan(z))] = 0.0 # ignore div by 0 NaN

    idx = z.argsort()
    x, y, z = x[idx], y[idx], z[idx]

    ax.scatter(x, y, s=0.1, c=z, cmap="Spectral_r", **kwargs)

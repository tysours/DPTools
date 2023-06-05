import os
import shutil
from ase.io import read

from dptools.cli import BaseCLI
from dptools.utils import tag_groups
from dptools.utils import get_seed as seed

class CLI(BaseCLI):
    """
    Shake atoms around for running multiple MD runs and improve sampling efficiency.
    :doc:`Complete documentation here<../commands/shake>`

    Examples:

    .. code-block:: console

        $ dptools shake structure.traj
        $ dptools shake -n 10 structure.traj
        $ dptools shake -d 0.05 -o shaken_atoms.traj structure.traj
        $ dptools shake -n 6 -a MOF_with_water_adsorbates.traj
    """
    help_info = "Shake atoms to generate unique starting points for multiple MD runs"
    def add_args(self):
        self.parser.add_argument(
            "structure",
            type=str,
            help="Path to structure input file (.traj, .xyz, etc.)"
        )
        self.parser.add_argument("-n", type=int, default=5,
                help="Number of new structures to write (repeat shake n times)")
        self.parser.add_argument("-d", "--displacement", type=float, default=0.01,
                help="Max displacement distance to shake each atom")
        self.parser.add_argument("-p", "--path", type=str, default=".",
                help="Path to directory to create new folders for each shaken structures")
        self.parser.add_argument("-o", "--output", type=str, default="start.traj",
                help="Name of new file to write in each directory")
        self.parser.add_argument("-a", "--adsorbate", action="store_true",
                help="If specified, identifies and shuffles adsorbates randomly "\
                "(i.e., -d is ignored for adsorbates)")

    def main(self, args):
        self.atoms = read(args.structure)
        self.n = args.n
        if args.adsorbate:
            self.shuffle_adsorbates()
        new_atoms = self.shake(dmax=args.displacement)
        self.write(new_atoms, args.path, args.output)

    def shake(self, dmax):
        new_atoms = []
        for _ in range(self.n):
            atoms = self.atoms.copy()
            atoms.rattle(dmax, seed=seed())
            new_atoms.append(atoms)
        return new_atoms

    def write(self, atoms, path, out_file):
        dir_dim = len(str(self.n)) if len(str(self.n)) > 3 else 3 # 000-999 unless n >= 1000
        shake_dirs = [f"{i:0{dir_dim}d}" for i in range(self.n)]
        paths = [os.path.join(path, d) for d in shake_dirs]
        for a, p in zip(atoms, paths):
            os.makedirs(p, exist_ok=True)
            a.write(os.path.join(p, out_file))

    def shuffle_adsorbates(self):
        raise NotImplementedError("Adsorbate shuffling coming soon-ish")

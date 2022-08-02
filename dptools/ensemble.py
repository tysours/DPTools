from dptools.utils import graph2typemap
from dptools.cli import BaseCLI

def get_dev(atoms, graphs, type_map=None):
    pos = np.array([a.get_positions().flatten() for a in atoms])
    cell = np.array([a.cell.array.flatten() for a in atoms])
    if not type_map:
        type_map = graph2typemap(graphs[0])
    types = [type_map[a.symbol] for a in atoms[0]]

    models = [DP(g) for g in graphs]

    dev = calc_model_devi(pos, cell, types, models, nopbc=False)[:, 4]
    return dev


class CLI(BaseCLI):
    def add_args(self):
        help="Snapshots from MD simulation to select new training configuraitons from (.traj or similar)"
        self.parser.add_argument(
            "configurations",
            help=help
        )

    def main(self, args):
        raise NotImplementedError("Coming soon...")

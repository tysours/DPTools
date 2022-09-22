from dptools.cli import BaseCLI
from dptools.utils import Converter

class CLI(BaseCLI):
    """
    Convert between structure ASE/VASP/LAMMPS file types.

    :doc:`Complete documentation here<../commands/convert>`

    Examples:

    .. code-block:: console

        $ dptools convert thing.cif thing.traj
        $ dptools convert md_000/vasprun.xml md_001/vasprun.xml full_md.traj
        $ dptools convert md_???/vasprun.xml full_md.traj # equivalent to above
        $ dptools convert -i ::10 vasprun.xml condensed_traj.traj
    """

    help_info = "Convert between structure file types (e.g., .xml to .db)"
    def add_args(self):
        self.parser.add_argument(
            "inputs",
            nargs="+",
            metavar="input",
            help="Input files (with extensions) to convert. Multiple inputs are concatenated into output",
        )
        self.parser.add_argument(
            "output",
            nargs=1,
            help="Output file name to write conversion to (with extension)",
        )
        self.parser.add_argument("-i", "--indices", type=str, default=":",
                help="Indices of input files to read. E.g., :10, -3:, :100:5")

    def main(self, args):
        converter = Converter(args.inputs, args.output[0], args.indices)
        self.get_kwargs(args.inputs)
        converter.convert(**self.kwargs)

    def get_kwargs(self, inputs):
        self.kwargs = {}
        if inputs[0].endswith(".dump"):
            from dptools.env import get_dpfaults
            graph, type_map = get_dpfaults()
            self.kwargs.setdefault("type_map", type_map)

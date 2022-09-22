from dptools.cli import BaseCLI
from dptools.simulate.parameters import get_parameter_sets, write_yaml

class CLI(BaseCLI):
    """
    Get params.yaml for specific simulation type.

    :doc:`Complete documentation here<../commands/get>`

    Examples:

    .. code-block:: console

        $ dptools get cellopt
        $ dptools get nvt-md
        $ dptools get nvt-md.900K # custom simulation params
    """
    help_info = "Get params.yaml for specific calculation type"
    def add_args(self):
        self.parser.add_argument(
            "calculation",
            nargs=1,
            type=str,
            help="Calculation type to generate params.yaml file "
            "(spe, opt, cellopt, nvt-md, npt-md, eos, vib)."
            "\nCan also specify label of saved calculations (e.g. nvt-md.label)",
        )

    def main(self, args):
        param_sets = get_parameter_sets()
        params = param_sets[args.calculation[0]]
        with open("params.yaml", "w") as file:
            write_yaml(params, file)
        return

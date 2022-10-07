from dptools.cli import BaseCLI
from dptools.env import load, clear, clear_model, set_default_sbatch
from dptools.hpc import hpc_defaults
from dptools.simulate.parameters import reset_params


# TODO: Add reset params or reset {calculation_type} (e.g. nvt-md) in case
#       user screws up parameter_sets.yaml (also prevent this from happening)
class CLI(BaseCLI):
    """
    Reset models or sbatch parameters for environments made using ``dptools set ...``.

    :doc:`Complete documentation here<../commands/reset>`

    Examples:

    .. code-block:: console

        $ dptools reset all
        $ dptools reset -m water all
        $ dptools reset sbatch
    """

    help_info = "Reset model or sbatch params for default or labeled dptools env"
    def add_args(self):
        self.parser.add_argument(
            "thing",
            type=str,
            choices=("all", "sbatch", "model", "params"),
            help="Thing to reset (delete or set to default if exists)"\
                " (all, sbatch, model)"
        )
        self.parser.add_argument("-m", "--model-label", type=str, default=None,
                help="Label of specific model to use (see dptools set -h)")

    def main(self, args):
        if args.model_label:
            load(args.model_label)

        if args.thing == "all":
            clear(all)
        elif args.thing == "sbatch":
            set_default_sbatch(warn=False)
        elif args.thing == "model":
            clear_model()
        elif args.thing == "params":
            reset_params()

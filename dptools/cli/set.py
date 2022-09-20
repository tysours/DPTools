from dptools.cli import BaseCLI
from dptools.env import set_model, set_sbatch, set_params, set_custom_env


class CLI(BaseCLI):
    """
    Set DP models, Slurm settings, calculation parameters, or deepmd-kit training parameters

    Detailed documentation at https://dptools.readthedocs.io/en/latest/commands/set.html

    Examples:

        dptools set /home/user/projects/dp_models/h2o.pb
        dptools set 00/graph.pb 01/graph.pb 02/graph.pb 03/graph.pb # ensemble
        dptools set -m water /home/user/projects/dp_models/h2o.pb
        dptools set -m hpc_para parallel_settings.sh
        dptools set -m hpc_serial serial_settings.sh
        dptools set params.yaml
        dptools set /path/to/in.json
    """
    help_info = "Set DP model defaults, calculation parameters, or sbatch settings"

    def add_args(self):
        _help = "Path to DP model, params.yaml, or {script}.sh to set as default.\n"\
             "Need .pb, .yaml, or .sh extension to set model, params, or sbatch, respectively."
        self.parser.add_argument(
            "thing",
            nargs="+",
            help=_help,
        )
        self.parser.add_argument("-m", "--model-label", type=str, default=None,
                help="Save model/sbatch with specific label to access during "\
                        "'dptools run -m {label} {calc} {structure}'")

    def main(self, args):
        if args.model_label:
            set_custom_env(args.model_label)
        for i, t in enumerate(args.thing):
            if t.endswith(".pb") and i > 0:
                self.set(t, n_model=i+1)
            else:
                self.set(t)

    def set(self, thing, **kwargs):
        """
        Set file parameters to .env or simulation parameters to yaml file.

        Note:
            Multiple .pb inputs allowed for setting model ensembles.

        Args:
            thing (str): Path to file you want to set (.pb, .sh, .yaml, or .json file).
        """
        ext2function = {"pb": set_model, "sh": set_sbatch, "yaml": set_params}
        ext = thing.split(".")[-1]
        if ext not in ext2function:
            raise TypeError(f"Unrecognized file type for {thing}. Try 'dptools set -h'")
        set_thing = ext2function[ext]
        set_thing(thing, **kwargs)

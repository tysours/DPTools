from dptools.cli import BaseCLI
from dptools.env import set_model, set_sbatch, set_params, set_custom_env


class CLI(BaseCLI): # XXX: Everything about this could surely be improved
    help_info = "Set DP model defaults, calculation parameters, or sbatch settings"
    def add_args(self):
        help="Path to DP model, params.yaml, or {script}.sh to set as default.\n"\
             "Need .pb, .yaml, or .sh extension to set model, params, or sbatch, respectively."
        self.parser.add_argument(
            "thing",
            nargs="+",
            help=help
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
        ext2function = {"pb": set_model, "sh": set_sbatch, "yaml": set_params}
        ext = thing.split(".")[-1]
        if ext not in ext2function:
            raise TypeError(f"Unrecognized file type for {thing}. Try 'dptools set -h'")
        self.set_thing = ext2function[ext]
        self.set_thing(thing, **kwargs)

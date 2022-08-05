from dptools.cli import BaseCLI
from dptools.env import set_model, set_sbatch, set_params


class CLI(BaseCLI): # XXX: Everything about this could surely be improved
    def add_args(self):
        help="Path to DP model, params.yaml, or {script}.sh to set as default.\n"\
             "Need .pb, .yaml, or .sh extension to set model, params, or sbatch, respectively."
        self.parser.add_argument(
            "thing",
            nargs="+",
            help=help
        )

    def main(self, args):
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

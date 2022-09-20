import glob
import re
from os.path import dirname, join, abspath

from dptools.cli import BaseCLI
from dptools.env import get_env, set_custom_env
from dptools.utils import str2typemap


class CLI(BaseCLI):
    """
    Display information on set DP models and Slurm parameters.

    https://dptools.rtfd.io/en/latest/commands/info.html

    Examples:
        dptools info # display all set environments
        dptools info -m water # display specific labelled environment
    """
    help_info = "Show loaded DP models and sbatch parameters"

    def add_args(self):
        self.parser.add_argument("-m", "--model-label", type=str, default=all,
                help="Label of specific model to use (see dptools set -h)")

    def main(self, args):
        self.keys = [
                "DPTOOLS_MODEL",
                 "DPTOOLS_TYPE_MAP",
                 "DPTOOLS_MODEL2",
                 "DPTOOLS_MODEL3",
                 "DPTOOLS_MODEL4",
                 "SBATCH_COMMENT"
             ]
        basedir = abspath(join(dirname(__file__), ".."))
        envs = sorted(glob.glob(f"{basedir}/.env*"))
        if args.model_label is not all:
            envs = [e for e in envs if e.endswith(args.model_label)]
        self.info = {}
        for env in envs:
            self.set_info(env)

        self.summarize()
        
    @staticmethod
    def get_env_name(env_file):
        """
        Get corresponding name for .env.* file, e.g. water from .env.water.

        Args:
            env_file (str): path to .env file to get corresponding label (name).

        Returns:
            label (str): name of environment that is appended to .env file.
        """
        pattern = ".env.[a-zA-Z0-9]+"
        if re.search(pattern, env_file):
            label = env_file.split(".")[-1]
        else:
            label = ""
        return label

    def set_info(self, env_file):
        """
        Get and set all env key-value info.

        Args:
            env_file (str): path to .env file to get and set info for.
        """
        label = self.get_env_name(env_file)
        if label:
            set_custom_env(label)
        else:
            label = "default"
        self.info[label] = get_env()

    def summarize(self):
        """Print out semi-formatted env info."""
        if not self.info:
            print("No info to display, try setting a model using:",
                    "\t dptools set /path/to/graph.pb")
        for env, vals in self.info.items():
            print("-" * 64)
            print(f"{env.upper()} env")
            print()
            self._print_kv(vals, "DPTOOLS_MODEL")
            self._print_kv(vals, "DPTOOLS_MODEL2")
            self._print_kv(vals, "DPTOOLS_MODEL3")
            self._print_kv(vals, "DPTOOLS_MODEL4")
            print()
            self._print_kv(vals, "DPTOOLS_TYPE_MAP")
            print()
            self._print_kv(vals, "SBATCH_COMMENT", fmt="{key}:\n{val}")
            print("-" * 64)
            print()

    @staticmethod
    def _print_kv(thing, key, fmt="{key}={val}"):
        val = thing.get(key)
        if "TYPE_MAP" not in key:
            if val:
                print(fmt.format(key=key, val=val))
        else:
            print("TYPE MAP:")
            if val:
                type_map = str2typemap(val)
                for k, v in type_map.items():
                    print(f"{k}\t{v}")
            else:
                print("NO MODEL SET")

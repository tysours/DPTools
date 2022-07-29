import os
import dotenv
from dptools.cli import BaseCLI
from dptools.utils import typemap2str, str2typemap, read_type_map, graph2typemap

def set_env(key, value):
    dotenv.set_key(env_file, key, value)

def get_dpfaults():
    """ like defaults but for dp (haha... ha..) """
    defaults = dotenv.dotenv_values(env_file)
    graph = defaults.get("DPTOOLS_MODEL", "./graph.pb")
    type_map = defaults.get("DPTOOLS_TYPE_MAP", None)
    return graph, type_map

def set_model(model):
    graph = os.path.abspath(model)
    type_map = graph2typemap(graph)
    type_map_str = typemap2str(type_map)
    set_env("DPTOOLS_MODEL", graph)
    set_env("DPTOOLS_TYPE_MAP", type_map_str)

def set_sbatch(script):
    raise NotImplementedError("Harass me for this if you need it")

def set_params(params):
    raise NotImplementedError("Harass me for this if you need it")

basedir = os.path.abspath(os.path.dirname(__file__))
env_file = os.path.join(basedir, ".env")

class CLI(BaseCLI):
    def add_args(self):
        help="Path to DP model, params.yaml, or {script}.sh to set as default.\n"\
             "Need .pb, .yaml, or .sh extension to set model, params, or sbatch, respectively."
        self.parser.add_argument(
            "thing",
            nargs=1,
            help=help
        )

    def main(self, args):
        self.what_am_i(args.thing[0])
        self.set(args.thing[0])

    def what_am_i(self, thing):
        ext2function = {"pb": set_model, "sh": set_sbatch, "yaml": set_params}
        ext = thing.split(".")[-1]
        if ext not in ext2function:
            raise TypeError(f"Unrecognized file type for {thing}. Try 'dptools set -h'")
        self.set = ext2function[ext]

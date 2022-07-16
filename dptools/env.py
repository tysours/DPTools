import os
import dotenv
from dptools.cli import BaseCLI
from dptools.utils import typemap2str, str2typemap, read_type_map

def set_env(graph, type_map):
    if isinstance(type_map, dict):
        type_map = typemap2str(type_map)
    elif isinstance(type_map, str):
        if type_map.endswith(".json"):
            type_map = typemap2str(read_type_map(type_map))
    dotenv.set_key(env_file, "DPTOOLS_MODEL", graph)
    dotenv.set_key(env_file, "DPTOOLS_TYPE_MAP", type_map)
    return

def get_dpfaults():
    """ like defaults but for dp (haha... ha..) """
    defaults = dotenv.dotenv_values(env_file)
    graph = defaults.get("DPTOOLS_MODEL", "./graph.pb")
    type_map = defaults.get("DPTOOLS_TYPE_MAP", None)
    return graph, type_map

basedir = os.path.abspath(os.path.dirname(__file__))
env_file = os.path.join(basedir, ".env")

class CLI(BaseCLI):
    def add_args(self):
        self.parser.add_argument(
            "model",
            nargs=1,
            help="Path to deepmd-kit .pb model to set as default"
        )

    def main(self, args):
        graph = os.path.abspath(args.model[0])
        type_map_str = typemap2str(graph2typemap(graph))
        set_env(graph, graph2typemap(graph))

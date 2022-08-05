import os
import socket
import dotenv

from dptools.cli import BaseCLI
from dptools.utils import typemap2str, str2typemap, read_type_map, graph2typemap
from dptools.hpc import hpc_defaults

basedir = os.path.abspath(os.path.dirname(__file__))
default_env_file = os.path.join(basedir, ".env")
env_file = default_env_file


def set_env(key, value):
    dotenv.set_key(env_file, key, value)


def get_env():
    values = dotenv.dotenv_values(env_file)
    return values


def set_custom_env(label):
    global env_file
    env_file = default_env_file + "." + label


def get_dpfaults(key="model"):
    """ like defaults but for dp (haha... ha..) """
    print(env_file)
    default_vals = get_env()

    if key == "model":
        keys = ["DPTOOLS_MODEL", "DPTOOLS_TYPE_MAP"]
        defaults = tuple([default_vals.get(k) for k in keys])

    elif key == "ensemble":
        keys = ["DPTOOLS_TYPE_MAP",
                "DPTOOLS_MODEL",
                "DPTOOLS_MODEL2",
                "DPTOOLS_MODEL3",
                "DPTOOLS_MODEL4"]
        defaults = tuple([default_vals.get(k) for k in keys])

    elif key == "sbatch":
        keys = ["SBATCH_COMMENT", 
                "OMP_NUM_THREADS", 
                "TF_INTRA_OP_PARALLELISM_THREADS", 
                "TF_INTER_OP_PARALLELISM_THREADS"]

        if not default_vals.get(keys[0], None):
            set_default_sbatch()
            default_vals = get_env()
        defaults = {k: default_vals[k] for k in keys}
    return defaults


def set_default_sbatch():
    host = socket.gethostname()
    try:
        print("WARNING: setting default HPC parameters to env")
        print("\nSettings:")
        print("-" * 64)
        for k, v in hpc_defaults[host].items():
            set_env(k, str(v))
            print(k, "=", v)
        print("-" * 64)
    except KeyError:
        raise Exception("Host unrecognized and no default HPC parameters found."\
            "\nUse 'dptools set script.sh' with desired #SBATCH comment in script.sh")
            # XXX: What kind of exception would this be?


def set_model(model, n_model=""):
    graph = os.path.abspath(model)
    set_env(f"DPTOOLS_MODEL{n_model}", graph)
    if not n_model: # only write type_map once if setting ensemble of models
        type_map = graph2typemap(graph)
        type_map_str = typemap2str(type_map)
        set_env(f"DPTOOLS_TYPE_MAP", type_map_str)


def set_sbatch(script):
    with open(script) as file:
        lines = [l.strip() for l in file]
    sbatch_vars = []
    for l in lines:
        if l.startswith("#SBATCH"):
            sbatch_vars.extend(l.split()[1:])
        elif l.startswith("export"):
            var = l.split()[1]
            set_env(*var.split("="))
    sbatch_comment = "#SBATCH " + " ".join(sbatch_vars)
    set_env("SBATCH_COMMENT", sbatch_comment)


def set_params(params):
    from dptools.simulate.parameters import set_parameter_set
    set_parameter_set(params)

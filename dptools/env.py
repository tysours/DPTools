"""
Functions for controlling different dptools env configurations
(deepmd models, sbatch parameters, etc.).
i.e. controls things set with CLI :doc:`../commands/set` command.

Mostly indented to be used behind the scenes with CLI commands, but theoretically could
be used in python scripts as well. Slightly confusing usage with global env_file (sorry),
so use at your own risk.
"""
import os
import json
import socket
import dotenv

from dptools.utils import typemap2str, graph2typemap
from dptools.hpc import hpc_defaults

basedir = os.path.abspath(os.path.dirname(__file__))
default_env_file = os.path.join(basedir, ".env")
env_file = default_env_file


def set_env(key, value):
    """Set key-value to global env file."""
    dotenv.set_key(env_file, key, value)


def get_env():
    """Get all key-values from global env file."""
    values = dotenv.dotenv_values(env_file)
    return values


def set_custom_env(label):
    """Sets global env file if different from default .env"""
    if label:
        global env_file
        env_file = default_env_file + "." + label


def get_dpfaults(key="model"):
    """
    Like defaults but for dp (haha... ha..). Loads specific key-values from env file.

    Args:
        key (str): ``(model, ensemble, sbatch)`` Gets env information from env file.
            * if key is set to model, return env's deepmd model path and type map
            * if key is set to ensemble, return all model paths belonging to env's ensemble
            * if key is set to sbatch, return env's Slurm settings
    """
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


def set_default_sbatch(warn=True):
    """
    Sets Slurm parameters from dptools.hpc.hpc_defaults. Mostly used by CLI when
    no Slurm info has been set to env.
    """
    host = socket.gethostname()
    try:
        for k, v in hpc_defaults[host].items():
            set_env(k, str(v))
        if warn:
            print("WARNING: setting default HPC parameters to env")
            print("-" * 64)
            print("\nSettings:")
            for k, v in hpc_defaults[host].items():
                print(k, "=", v)
            print("-" * 64)
    except KeyError as exc:
        raise Exception("Host unrecognized and no default HPC parameters found."\
            "\nUse 'dptools set script.sh' with desired #SBATCH comment in script.sh") from exc


def clear(keys):
    """
    Clear specific key-values (or entire env) for loaded global env file.
    """
    if keys is all:
        os.remove(env_file)
    else:
        vals = get_env()
        for key in keys:
            if vals.get(key):
                dotenv.unset_key(env_file, key)


def clear_model():
    """
    Clear model related key-values from loaded global env file.
    """
    keys = [
            "DPTOOLS_TYPE_MAP",
            "DPTOOLS_MODEL",
            "DPTOOLS_MODEL2",
            "DPTOOLS_MODEL3",
            "DPTOOLS_MODEL4",
        ]
    clear(keys)


def set_model(model, n_model=""):
    """
    Set path to deepmd model .pb file to use during simulations evoked by CLI
    :doc:`../commands/run` command.
    """
    if not n_model:
        clear_model()
    graph = os.path.abspath(model)
    set_env(f"DPTOOLS_MODEL{n_model}", graph)
    if not n_model: # only write type_map once if setting ensemble of models
        type_map = graph2typemap(graph)
        type_map_str = typemap2str(type_map)
        set_env("DPTOOLS_TYPE_MAP", type_map_str)


def set_sbatch(script):
    """
    Reads script and searches for any #SBATCH line to set to env file.

    Args:
        script (str): Path to .sh script with #SBATCH comments to set Slurm params.
    """
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
    """
    Save set of simulation parameters to run with CLI :doc:`../commands/run` command.
    """
    from dptools.simulate.parameters import set_parameter_set
    set_parameter_set(params)


def set_training_params(in_json):
    """
    Save deepmd-kit training parameters to use with CLI :doc:`../commands/train` command.
    """
    if isinstance(in_json, str):
        with open(in_json) as file:
            in_json = json.loads(file.read())
    if not in_json.get("model"):
        # check if correct param file/dict was given before overwriting default file
        raise KeyError("No model parameters found in json file.")

    # no need to keep these values since they will be overwritten anyway
    in_json["model"]["type_map"] = []
    in_json["training"]["training_data"]["systems"] = []
    in_json["training"]["validation_data"]["systems"] = []

    path = os.path.join(basedir, "train/in.json")
    with open(path, "w") as file:
        file.write(json.dumps(in_json, indent=4))

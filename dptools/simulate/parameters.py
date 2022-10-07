"""
Functions for interacting with simulation parameter files (.yaml).
If adding a new simulation parameter, add a description/usage hint to
dptools.parameters.descriptions, and the hint will appear in params.yaml.
"""
import os
import requests
from ruamel.yaml import YAML

basedir = os.path.abspath(os.path.dirname(__file__))
param_file = os.path.join(basedir, "parameter_sets.yaml")

descriptions = {
    "type": "Type of calculation (spe, opt, cellopt, nvt-md, npt-md, eos)",
    "disp_freq": "Print lammps output every {disp_freq} steps (thermo disp_freq)",
    "nsw": "Max number of iterations",
    "ftol": "Force convergence tolerance for lammps minimize",
    "etol": "Energy convergence tolerance for lammps minimize",
    "opt_type": "(iso, aniso, tri) see https://docs.lammps.org/fix_box_relax.html",
    "Ptarget": "Desired pressure [bar]",
    "steps": "Total number of timesteps to run simulation",
    "timestep": "[fs]",
    "equil_steps": "Number of timesteps to run initial equilibration at Ti",
    "Ti": "Initial temperature [K] at start of simulation",
    "Tf": "Final temperature [K] of simulation (ramped from Ti to Tf)",
    "Pi": "Initial pressure [bar] at start of simulation",
    "Pf": "Final pressure [bar] of simulation (ramped from Pi to Pf)",
    "pre_opt": "Optimize structure (and cell for npt-md) before starting MD run",
    "write_freq": "Write MD image every {write_freq} steps",
    "N": "Create N equally spaced structures with cell Volumes from V0*lo to V0*hi",
    "lo": "Lower bound for cell deformations (min volume = lo * V0)",
    "hi": "Upper bound for cell deformations (max volume = hi * V0)",
    "nfree": "(2 or 4) Number of displacements for each degree of freedom",
    "delta": "Magnitude of each displacement [Å]",
}


def write_yaml(param_dict, file):
    """
    Write simulation parameter set to yaml file. Used by the :doc:`../commands/get` to
    retrieve params.yaml files for specific simulation to be edited and then either used
    with :doc:`../commands/set` or :doc:`../commands/run` command.

    Args:
        param_dict (dict): Dictionary containing each parameter and its
            corresponding value.
        file (file object): File to write simulation parameter set to
            (generally params.yaml)
    """
    lengths = [len(k) + len(str(v)) for k, v in param_dict.items()]
    column = max(lengths) + 4  # align parameter description comments
    for param in param_dict:
        description = descriptions.get(param, f"No description available for parameter '{param}'")
        param_dict.yaml_add_eol_comment(description, key=param, column=column)
    YAML().dump(param_dict, file)


def get_parameter_sets():
    """
    Load simulation parameter sets from parameter_sets.yaml.
    """
    with open(param_file) as file:
        parameter_sets = YAML().load(file.read())
    return parameter_sets


def set_parameter_set(param_dict):
    """
    Write simulation parameter set to parameter_sets.yaml for future use.

    Args:
        param_dict (dict): Dictionary containing each parameter and its
            corresponding value.
    """
    if isinstance(param_dict, str):
        with open(param_dict) as file:
            param_dict = YAML(typ="safe").load(file.read())
    parameter_sets = get_parameter_sets()
    calc_type = param_dict.get("type")
    parameter_sets[calc_type] = param_dict
    with open(param_file, "w") as file:
        YAML().dump(parameter_sets, file)


def reset_params():
    url = "https://github.com/tysours/DPTools/raw/main/dptools/simulate/parameter_sets.yaml"
    req = requests.get(url, allow_redirects=True)
    parameter_sets = YAML().load(req.content)
    with open(param_file, "w") as file:
        YAML().dump(parameter_sets, file)

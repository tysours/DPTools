from ruamel.yaml import YAML
import os

from dptools.cli import BaseCLI


def write_yaml(param_dict, file):
    lengths = [len(k) + len(str(v)) for k, v in param_dict.items()]
    column = max(lengths) + 4  # align parameter description comments
    for param in param_dict:
        param_dict.yaml_add_eol_comment(descriptions[param], key=param, column=column)
    YAML().dump(param_dict, file)
    return


def get_parameter_sets():
    basedir = os.path.abspath(os.path.dirname(__file__))
    param_file = os.path.join(basedir, "parameter_sets.yaml")
    with open(param_file) as file:
        parameter_sets = YAML().load(file.read())
    return parameter_sets


def set_parameter_set(param_dict):
    if isinstance(param_dict, str):
        with open(param_dict) as file:
            param_dict = YAML(typ="safe").load(file.read())
    basedir = os.path.abspath(os.path.dirname(__file__))
    param_file = os.path.join(basedir, "parameter_sets.yaml")
    parameter_sets = get_parameter_sets()
    calc_type = param_dict.get("type")
    parameter_sets[calc_type] = param_dict
    with open(param_file, "w") as file:
        YAML().dump(parameter_sets, file)


descriptions = {
    "type": "Type of calculation (spe, opt, cellopt, nvt-md, npt-md)",
    "disp_freq": "Print lammps output every {disp_freq} steps (thermo disp_freq)",
    "nsw": "Max number of iterations",
    "ftol": "Force convergence tolerance for lammps optimize",
    "etol": "Energy convergence tolerance for lammps optimize",
    "opt_type": "(iso, aniso, tri) see https://docs.lammps.org/fix_box_relax.html",
    "Ptarget": "Desired pressure [eV/Å]",
    "steps": "Total number of timesteps to run simulation",
    "timestep": "[fs]",
    "equil_steps": "Number of timesteps to run initial equilibration at Ti",
    "Ti": "Initial temperature [K] at start of simulation",
    "Tf": "Final temperature [K] of simulation (ramped from Ti to Tf)",
    "Pi": "Initial pressure [bar] at start of simulation",
    "Pf": "Final pressure [bar] of simulation (ramped from Pi to Pf)",
    "pre_opt": "Optimize structure (and cell for npt-md) before starting MD run",
    "write_freq": "Write MD image every {write_freq} steps",
}

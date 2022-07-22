from ruamel.yaml import YAML
import json
import sys

from dptools.cli import BaseCLI

def write_yaml(param_dict, file):
    lengths = [len(k) + len(str(v)) for k, v in param_dict.items()]
    column = max(lengths) + 4 # align parameter description comments
    for param in param_dict:
        param_dict.yaml_add_eol_comment(
                descriptions[param],
                key=param,
                column=column
                )
    YAML().dump(param_dict, file)
    return

def get_parameter_sets():
    basedir = os.path.abspath(os.path.dirname(__file__))
    param_file = os.path.join(basedir, "parameter_sets.yaml")
    with open(param_file) as file:
        parameter_sets = YAML().load(file.read())
    return parameter_sets
        
descriptions = {
        "type": "Type of calculation (spe, opt, cellopt, nvt-md, npt-md)",
        "nsw": "Max number of iterations",
        "ftol": "Force convergence tolerance for lammps optimize",
        "etol": "Energy convergence tolerance for lammps optimize",
        "opt_type": "(iso, aniso, tri) see https://docs.lammps.org/fix_box_relax.html",
        "Ptarget": "Desired pressure (eV/Å)",
        "Ti": "Initial temperature (K) at start of simulation",
        "Tf": "Final temperature (K) of simulation (ramped form Ti to Tf)"
    }

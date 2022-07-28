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
    "Tf": "Final temperature [K] of simulation (ramped form Ti to Tf)",
    "pre_opt": "Optimize structure (and cell for npt-md) before starting MD run",
    "write_freq": "Write MD image every {write_freq} steps",
}


class CLI(BaseCLI):
    def add_args(self):
        self.parser.add_argument(
            "calculation",
            nargs=1,
            type=str,
            help="Calculation type to generate params.yaml file "
            "(spe, opt, cellopt, nvt-md, npt-md)."
            "\nCan also specify label of saved calculations (e.g. nvt-md.label)",
        )

    def main(self, args):
        param_sets = get_parameter_sets()
        params = param_sets[args.calculation[0]]
        with open("params.yaml", "w") as file:
            write_yaml(params, file)
        return

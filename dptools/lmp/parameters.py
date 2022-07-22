from ruamel.yaml import YAML
import ruamel.yaml
import json
import sys

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
        
descriptions = {
        "type": "Type of calculation (spe, opt, cellopt, nvt-md, npt-md)",
        "nsw": "Max number of iterations",
        "ftol": "Force convergence tolerance for lammps optimize",
        "celltype": "Thing guy man bro",
        "Ti": "(K) Initial temperature at start of simulation",
        "Tf": "(K) Final temperature of simulation (ramped form Ti to Tf)"
    }

#with open('test.json') as file:
with open('test.yaml') as file:
    #test = round_trip_load(file.read())
    test = YAML().load(file.read())

with open("params.yaml", "w") as file:
    write_yaml(test["cellopt"], file)

test = ruamel.yaml.round_trip_load(ruamel.yaml.round_trip_dump(test["cellopt"]))
for k in test:
    print(descriptions[k])
    test.yaml_add_eol_comment(
            descriptions[k],
            key=k,
            column=20
            )
YAML().dump(test, sys.stdout)
'''
test.yaml_set_comment_before_after_key(key='type', before=descriptions['type'])
with open('wat.yaml', 'w') as file:
#    ruamel.yaml.round_trip_dump(test, file)#sys.stdout)
    ruamel.yaml.YAML().dump(test, file)
'''
'''
a = {'nsw': 100, 'Ti': 298, 'Tf': 1999}

with open('test.yaml', 'w') as file:
    ruamel.yaml.safe_dump(a, file, default_flow_style=False, 
            sort_keys=False, allow_unicode=True)
'''

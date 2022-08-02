import os

# defaults for Kulkarni group hpc systems
hpc_defaults = {
        "cori10": {
            "SBATCH_COMMENT": "#SiBATCH not implemented yet",
            "OMP_NUM_THREADS": "1",
            "TF_INTRA_OP_PARALLELISM_THREADS": "1",
            "TF_INTER_OP_PARALLELISM_THREADS": "1"
            },
        "hpc1": {
            "SBATCH_COMMENT": "#SBATCH --partition=med -N 1 --ntasks-per-node=8 --output=job.out --error=job.err -t 96:00:00",
            "OMP_NUM_THREADS": "8",
            "TF_INTRA_OP_PARALLELISM_THREADS": "6",
            "TF_INTER_OP_PARALLELISM_THREADS": "2"
            },
        "hpc2": {
            "SBATCH_COMMENT": "#SBATCH --partition=med -N 1 --ntasks-per-node=8 --output=job.out --error=job.err -t 96:00:00",
            "OMP_NUM_THREADS": "8",
            "TF_INTRA_OP_PARALLELISM_THREADS": "6",
            "TF_INTER_OP_PARALLELISM_THREADS": "2"
            },
        }

# TODO: Split sbatch into n_nodes, n_tasks_per_node, etc.
class SlurmJob:
    def __init__(self, 
                 sbatch_comment,
                 commands="",
                 directories=".",
                 file_name="script.sh",
                 **kwargs
                 ):

        self.sbatch = sbatch_comment
        self.commands = commands
        self.set_path_stuff(directories, file_name) # what's the term for this? setting directories + file_name + full path
        self.set_text(**kwargs)

    def get_header(self):
        header = f"#!/usr/bin/env bash\n{self.sbatch}\n"
        return header

    def set_path_stuff(self, directories, file_name):
        if isinstance(directories, str):
            directories = [directories]
        self.directories = [os.path.abspath(d) for d in directories]
        self.file_name = file_name
        self.paths = [os.path.join(d, file_name) for d in self.directories]

    def set_text(self, **kwargs):
        header = self.get_header()

        exports = ""
        for k, v in kwargs.items():
            exports += f"export {k}={v}\n"

        body = "\n"
        if isinstance(self.commands, list):
            for comm in self.commands:
                body += comm + "\n"
        elif isinstance(self.commands, str):
            body += self.commands

        self.text = header + exports + body

    def _write_file(self, path):
        with open(path, "w") as file:
            file.write(self.text)

    def write(self, sub=False):
        for directory, path in zip(self.directories, self.paths):
            self._write_file(path)
            if sub:
                os.chdir(directory)
                os.system(f"sbatch {self.file_name}")

    def submit(self):
        self.write(sub=True)

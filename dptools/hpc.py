"""
Module for controlling HPC job submissions. Currently only supports Slurm jobs.
"""
import os

# defaults for Kulkarni group hpc systems
hpc_defaults = {
        "cori": {
            "SBATCH_COMMENT": "#SBATCH -J job -q shared -N 1 -t 11:00:00 "\
                "-C haswell --output=job.out --error=job.err --ntasks=1 -c 1",
            "OMP_NUM_THREADS": "1",
            "TF_INTRA_OP_PARALLELISM_THREADS": "1",
            "TF_INTER_OP_PARALLELISM_THREADS": "1"
            },
        "hpc": {
            "SBATCH_COMMENT": "#SBATCH --partition=med -N 1 --ntasks-per-node=8 "\
                "--output=job.out --error=job.err -t 96:00:00",
            "OMP_NUM_THREADS": "8",
            "TF_INTRA_OP_PARALLELISM_THREADS": "6",
            "TF_INTER_OP_PARALLELISM_THREADS": "2"
            },
        }

# TODO: Split sbatch into n_nodes, n_tasks_per_node, etc.
class SlurmJob:
    """
    Sets up and optionally submits slurm job scripts on HPC systems. Default settings for
    your HPC system can be added to dptools.hpc.hpc_defaults, or controlled using the
    CLI :doc:`../commands/set` command.

    .. role:: python(code)
        :language: python

    Args:
        sbatch_comment (str): Single line containing all Slurm #SBATCH parameters.
            e.g., :python:`'#SBATCH -J job -q regular -N 1 --time=11:00:00'`

        directories (list[str] or str): Path(s) to job submission directories.

        file_name (str): Name of submission script to write. Currently only supports .sh scripts,
            but support for others (e.g., .py) can be easily added upon request.

        zip_commands (bool): Set to True if each submission dir requires a unique set of commands.
            If True, then len(commands) must equal len(directories), and each item in commands
            is used for the respective directory index. i.e., job scripts are written as,

            .. code-block:: python

                for command, dir in zip(commands, directories):
                    write_script(command=command, submission_dir=dir)

            If False, then the same command(s) is used in all submission directories.

        **kwargs: Unpacked dict containing any env variables to set in submission script.
            e.g. :python:`kwargs = dict(TF_INTRA_OP_PARALLELISM_THREADS="1")` adds this
            line to .sh script,

            .. code-block:: bash

                export TF_INTRA_OP_PARALLELISM_THREADS=1
    """
    def __init__(self,
                 sbatch_comment,
                 commands="",
                 directories=".",
                 file_name="script.sh",
                 zip_commands=False,
                 **kwargs
                 ):

        self.sbatch = sbatch_comment
        self._zip = zip_commands
        self.commands = commands
        self.set_path_stuff(directories, file_name)
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
        if not self._zip and isinstance(self.commands, list):
            for comm in self.commands:
                body += comm + "\n"
        elif isinstance(self.commands, str):
            body += self.commands

        else:    # do not write commands to body if self._zip
            pass # in this case, self.commands contains
                 # list of unique commands for each submission dir

        self.text = header + exports + body

    @property
    def text(self):
        if self._zip:
            return self._text + next(self.comm_generator)
        return self._text

    @text.setter
    def text(self, new_text):
        self._text = new_text
        if self._zip:
            self.comm_generator = self.generate_commands()

    def generate_commands(self):
        for comm in self.commands:
            yield comm

    def write_script(self, path):
        with open(path, "w") as file:
            file.write(self.text)

    def write(self, sub=False):
        for directory, path in zip(self.directories, self.paths):
            self.write_script(path)
            if sub:
                os.chdir(directory)
                os.system(f"sbatch {self.file_name}")

    def submit(self):
        self.write(sub=True)

===
run
===

General usage,

.. code-block:: console

   $ dptools run [-h] [-m MODEL_LABEL] [-s] [-g] [-o OUTPUT] calculation structure [structure ...]

.. code-block:: bash

   positional arguments:
     calculation           Type of calculation to run (spe, opt, cellopt, nvt-md, npt-md, eos, vib, or params.yaml)
     structure             File containing structure to run calculation on (.traj, .xyz, .cif, etc.)
   
   optional arguments:
     -h, --help            show this help message and exit
     -m MODEL_LABEL, --model-label MODEL_LABEL
                           Label of specific model to use (see dptools set -h) (default: None)
     -s, --submit          Automatically submit job(s) to train model(s) once input has been created (default: False)
     -g, --generate-input  Only setup calculation and generate input files but do not run calculation (default: False)
     -o OUTPUT, --output OUTPUT
                           Name of file to write calculation output to (default: {calculation}.traj)


Quick reference examples
------------------------

.. code-block:: console

   $ dptools run opt start.traj # simple atomic position optimization
   $ dptools run cellopt start.traj # simple unit cell optimization
   $ dptools run /path/to/params.yaml start.traj # custom param file simulation
   $ dptools run -s eos 0*/start.traj # submit slurm job eos simulations on multiple structures
   $ dptools run -s -m water nvt-md start.traj # submit slurm nvt-md run using set water model


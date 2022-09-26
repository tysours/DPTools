===
run
===

General usage,

.. code-block:: console

   $ dptools run [-h] [-m MODEL_LABEL] [-s] [-g] [-o OUTPUT] calculation structure [structure ...]

Quick reference examples
------------------------

.. code-block:: console

   $ dptools run opt start.traj # simple atomic position optimization
   $ dptools run cellopt start.traj # simple unit cell optimization
   $ dptools run /path/to/params.yaml start.traj # custom param file simulation
   $ dptools run -s eos 0*/start.traj # submit slurm job eos simulations on multiple structures
   $ dptools run -s -m water nvt-md start.traj # submit slurm nvt-md run using set water model


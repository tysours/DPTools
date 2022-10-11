===
set
===

The ``dptools set`` command is one of the most used commands in DPTools!
It is used to save various system configurations:

* deepmd-kit models (.pb files)
* HPC (slurm) parameters (.sh files)
* simulation parameters (.yaml files)
* deepmd training parameters (.json files)

General usage,

.. code-block:: console

   $ dptools set [-h] [-m MODEL_LABEL] thing [thing ...]

.. code-block:: bash

   positional arguments:
     thing                 Path to DP model, params.yaml, or {script}.sh to set as default. Need .pb, .yaml, or .sh extension to set model, params, or sbatch, respectively.
   
   optional arguments:
     -h, --help            show this help message and exit
     -m MODEL_LABEL, --model-label MODEL_LABEL
                           Save model/sbatch with specific label to access during 'dptools run -m {label} {calc} {structure}' (default: None)


.. note::

   To see information on all set models and sbatch parameters, use the ``dptools info``
   command.


Quick reference examples
------------------------

.. code-block:: console

   $ dptools set /home/user/projects/dp_models/h2o.pb
   $ dptools set 00/graph.pb 01/graph.pb 02/graph.pb 03/graph.pb # ensemble
   $ dptools set -m water /home/user/projects/dp_models/h2o.pb
   $ dptools set -m hpc_para parallel_settings.sh
   $ dptools set -m hpc_serial serial_settings.sh
   $ dptools set params.yaml
   $ dptools set /path/to/in.json


.. _set_model: 

Set default DP model
--------------------

Setting a DP model (.pb tensorflow graph file) allows you to :doc:`run` a simulation.
Just supply the path to the model file,

.. code-block:: console

   $ dptools set /path/to/graph.pb

This model will now be used as the default for ``dptools run``.


Set labelled DP model
---------------------

If you're working with multiple DP models (e.g. for two different projects with different systems
or for comparing two different model architectures for the same system), you can set additional
models with a specific label. 

.. code-block:: console

   $ dptools set -m label /path/to/graph.pb

The label can now be used to specify the model when you :doc:`run` simulations, like for example,

.. code-block:: console

   $ dptools run -m label opt start.traj


.. _set_ensemble: 

Set ensemble of DPs
-------------------

If you want to set an ensemble of model to use for :doc:`sampling new configurations for
training<sample>`, you can set the ensemble by specifying the paths to each DP model,

.. code-block:: console

   $ dptools set 00/graph.pb 01/graph.pb 02/graph.pb 03/graph.pb

You can also set a label for your ensemble in the same way you do for a single model,

.. code-block:: console

   $ dptools set -m iteration2_ensemble 00/graph.pb 01/graph.pb 02/graph.pb 03/graph.pb

.. note::

   You must specify all model files in a single command to set an ensemble.
   If you try to set them individually like,

   .. code-block:: console

      $ dptools set 00/graph.pb # don't do this!
      $ dptools set 01/graph.pb # don't do this!
   
   The ``01/graph.pb`` is **not** appended to a list of models! You are simply replacing
   ``00/graph.pb`` with ``01/graph.pb``.


.. _mod_params:

Modify default simulation parameters
------------------------------------

To change the default simulation parameters for any simulation type, retrieve the corresponding
params.yaml file with the :doc:`get` command. To modify the ``nvt-md`` parameters for example,

.. code-block:: console

   $ dptools get nvt-md

Edit the params.yaml file in whatever text editor you prefer, and then set the file,

.. code-block:: console

   $ dptools set params.yaml

These new parameters will now be used everytime you :doc:`run` the simulation,

.. code-block:: console

   $ dptools run nvt-md start.traj


.. _set_custom:

Create custom simulation parameter sets
---------------------------------------

This is useful if you want to store multiple parameter settings for the same type of simulation
so you don't have to constantly retrieve and modify params.yaml files if you'll be using these
settings frequently.

For example, let's say you want to store several different temperature settings for an NVT-MD
simulation. First :doc:`get` the params.yaml file for the ``nvt-md`` simulation,

.. code-block:: console

   $ dptools get nvt-md

Opening the params.yaml file will look something like,

.. code-block:: yaml

   type: nvt-md        # Type of calculation (spe, opt, cellopt, nvt-md, npt-md, eos)
   steps: 100000       # Total number of timesteps to run simulation
   timestep: 0.5       # [fs]
   Ti: 298.0           # Initial temperature [K] at start of simulation
   Tf: 298.0           # Final temperature [K] of simulation (ramped from Ti to Tf)
   equil_steps: 10000  # Number of timesteps to run initial equilibration at Ti
   write_freq: 100     # Write MD image every {write_freq} steps
   disp_freq: 100      # Print lammps output every {disp_freq} steps (thermo disp_freq)
   pre_opt: false      # Optimize structure (and cell for npt-md) before starting MD run

.. role:: yaml(code)
    :language: yaml

To create a custom parameter set for :yaml:`type: nvt-md`, modify the type name following the
format :yaml:`type: nvt-md.label`. **You must retain the original simulation type name
before the appended label!** 

Let's make a new set of parameters for 600 K by modifying the params.yaml file like so,

.. code-block:: yaml
   :emphasize-lines: 1,4,5

   type: nvt-md.600K   # Type of calculation (spe, opt, cellopt, nvt-md, npt-md, eos)
   steps: 100000       # Total number of timesteps to run simulation
   timestep: 0.5       # [fs]
   Ti: 600.0           # Initial temperature [K] at start of simulation
   Tf: 600.0           # Final temperature [K] of simulation (ramped from Ti to Tf)
   equil_steps: 10000  # Number of timesteps to run initial equilibration at Ti
   write_freq: 100     # Write MD image every {write_freq} steps
   disp_freq: 100      # Print lammps output every {disp_freq} steps (thermo disp_freq)
   pre_opt: false      # Optimize structure (and cell for npt-md) before starting MD run

Now we can save the file and set it as usual,

.. code-block:: console

   $ dptools set params.yaml

And the simulation is now available for use directly with the :doc:`run` command!

.. code-block:: console

   $ dptools run nvt-md.600K start.traj

To expand on this example and demonstrate why this might be useful, let's repeat this
for 400 K and 800 K. Follow the same steps above, and now when we run ``dptools get list``,
we will see our new custom simulations,

.. code-block:: console

   $ dptools get list

   # Available calculation types:
   spe
   opt
   cellopt
   nvt-md
   npt-md
   eos
   vib
   nvt-md.600K
   nvt-md.400K
   nvt-md.800K
   
Now say we have several systems, such as 3 different metal-organic frameworks
(which probably wouldn't be stable at 800 K, but we'll ignore that), that we want
to :doc:`run` separate NVT-MD simulations at these 3 temperatures. Our
folder structure might look something like:

.. code-block:: bash

   .
   |-- 00_mof0
   |   |-- 400
   |   |   `-- mof0_start.traj
   |   |-- 600
   |   |   `-- mof0_start.traj
   |   `-- 800
   |       `-- mof0_start.traj
   |-- 01_mof1
   |   |-- 400
   |   |   `-- mof1_start.traj
   |   |-- 600
   |   |   `-- mof1_start.traj
   |   `-- 800
   |       `-- mof1_start.traj
   `-- 02_mof2
       |-- 400
       |   `-- mof2_start.traj
       |-- 600
       |   `-- mof2_start.traj
       `-- 800
           `-- mof2_start.traj

Note that all ``mof0_start.traj`` are equivalent structures (same for mof1 and mof2), we
just need a separate file in each directory to pass as an argument to ``dptools run`` (#TODO:
modify things to allow for multiple simulations stemming from a single input structure file).

Assuming we have already :ref:`set a model<set_model>` and :ref:`Slurm settings<set_sbatch>`.
We are now ready to submit these simulations to run! Simply use these 3 commands specifying our
custom temperature simulations:

.. code-block:: bash

   $ dptools run -s nvt-md.400K 0*/400/*start.traj
   $ dptools run -s nvt-md.600K 0*/600/*start.traj
   $ dptools run -s nvt-md.800K 0*/800/*start.traj


.. _set_sbatch:

Set Slurm parameters
--------------------

.. _set_training:

Set new training parameters
---------------------------

To change the default deepmd-kit training parameters, first retreive the in.json file using
the :doc:`get` command,

.. code-block:: console

   $ dptools get in.json

Edit the file in whatever text editor you prefer, and then set the file,

.. code-block:: console

   $ dptools set in.json

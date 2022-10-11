======
sample
======

.. important::

   Using ``dptools sample`` requires an ensemble (typically 4) of trained DP models!
   See :ref:`how to train an ensemble<train_ensemble>` and then :ref:`how to set the
   ensemble.<set_ensemble>`


General usage,

.. code-block:: console

   $ dptools sample [-h] [-m MODEL_ENSEMBLE [MODEL_ENSEMBLE ...]] [-n N] [--lo LO] [--hi HI] [-o OUTPUT] [-p] [--plot-steps] configurations [configurations ...]

.. code-block:: bash
   
   positional arguments:
     configurations        Snapshots from MD simulation to select new training configuraitons from (.traj or similar)
   
   optional arguments:
     -h, --help            show this help message and exit
     -m MODEL_ENSEMBLE [MODEL_ENSEMBLE ...], --model-ensemble MODEL_ENSEMBLE [MODEL_ENSEMBLE ...]
                           Paths to ensemble of models or label of set models (default: None)
     -n N                  Max number of new configurations to select (default: 300)
     --lo LO               Min value of eps_t (force dev) to select new configs from (default: 0.05)
     --hi HI               Max value of eps_t (force dev) to select new configs from (default: 0.35)
     -o OUTPUT, --output OUTPUT
                           File to write new configurations to (default: new_configs.traj)
     -p, --plot-dev        Plot histogram of max force deviation of model ensemble for each config (default: False)
     --plot-steps          Plot dev versus number of steps (default: False)


Quick reference examples
------------------------

.. code-block:: console

   $ dptools sample -n 200 nvt-md.traj
   $ dptools sample -n 100 --lo 0.05 --hi 0.25 nvt-md.traj
   $ dptools sample -m water_ensemble -p npt-md.traj
   $ dptools sample -o configs.traj nvt-md.traj

Basic usage
-----------



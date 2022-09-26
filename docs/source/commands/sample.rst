======
sample
======

.. important::

   Using ``dptools sample`` requires an ensemble (typically 4) of trained DP models!
   See [ref to train] to see how to automatically train an ensemble and [ref to set]
   to see how to set the ensemble.


General usage,

.. code-block:: console

   $ dptools sample [-h] [-m MODEL_ENSEMBLE [MODEL_ENSEMBLE ...]] [-n N] [--lo LO] [--hi HI] [-o OUTPUT] [-p] configurations [configurations ...]
   

Quick reference examples
------------------------

.. code-block:: console

   $ dptools sample -n 200 nvt-md.traj
   $ dptools sample -n 100 --lo 0.05 --hi 0.25 nvt-md.traj
   $ dptools sample -m water_ensemble -p npt-md.traj
   $ dptools sample -o configs.traj nvt-md.traj

Basic usage
-----------



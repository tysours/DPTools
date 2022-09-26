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

.. note::

   To see information on all set models and sbatch parameters, use the :doc:

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

DP Models
---------

Setting a DP model (tensorflow .pb file) allows you to easily run simulations without
having to constantly specify a model path when using the ``dptools run ...`` command

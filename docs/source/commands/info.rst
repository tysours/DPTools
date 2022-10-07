====
info
====

The ``dptools info`` command is used to display information on all deepmd models
and Slurm parameter settings that have been :doc:`set`.

General usage,

.. code-block:: console

   $ dptools info [-h] [-m MODEL_LABEL]

Quick reference examples
------------------------

.. code-block:: console

   $ dptools info # display all set environments
   $ dptools info -m water # display specific labelled environment

Display all saved model environments
------------------------------------

Simply running the command,

.. code-block:: console

   $ dptools info

will print all of the saved deepmd models and Slurm parameters for each environment
created by the :doc:`set` command.

The output will look something like:

.. code-block:: bash

   ----------------------------------------------------------------
    default env

    DPTOOLS_MODEL=/home/sours/data/dptools_stuff/mofs/02_iter2/01_train/00/graph.pb
    DPTOOLS_MODEL2=/home/sours/data/dptools_stuff/mofs/02_iter2/01_train/01/graph.pb
    DPTOOLS_MODEL3=/home/sours/data/dptools_stuff/mofs/02_iter2/01_train/02/graph.pb
    DPTOOLS_MODEL4=/home/sours/data/dptools_stuff/mofs/02_iter2/01_train/03/graph.pb

    TYPE MAP:
    C	0
    H	1
    O	2
    Zr	3

    SBATCH_COMMENT:
    #SBATCH --time=30:00:00 --nodes=1 --partition=med --ntasks-per-node=16 --output=job.out --error=job.err
    ----------------------------------------------------------------

    ----------------------------------------------------------------
    zeos env

    DPTOOLS_MODEL=/home/sours/data/univ_ml/datasets/00_zeolites/tuning/all/final/32/graph.pb

    TYPE MAP:
    O	0
    Si	1

    SBATCH_COMMENT:
    #SBATCH --time=30:00:00 --nodes=1 --partition=med --ntasks-per-node=16 --output=job.out --error=job.err
    ----------------------------------------------------------------

.. note::

   If you set too many models and you want to clear some of them, use the :doc:`reset` command!

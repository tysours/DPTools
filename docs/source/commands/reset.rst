=====
reset
=====

General usage,

.. code-block:: console

   $ dptools reset [-h] [-m MODEL_LABEL] {all,sbatch,model}

.. code-block:: bash

   positional arguments:
     {all,sbatch,model,params}
                           Thing to reset (delete or set to default if exists) (all, sbatch, model)
   
   optional arguments:
     -h, --help            show this help message and exit
     -m MODEL_LABEL, --model-label MODEL_LABEL
                           Label of specific model to use (see dptools set -h) (default: None)


Quick reference examples
------------------------

.. code-block:: console

    $ dptools reset all
    $ dptools reset -m water all
    $ dptools reset sbatch

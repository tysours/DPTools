=====
train
=====

General usage,

.. code-block:: console

   $ dptools train [-h] [-e] [-s] [-p PATH] [-i INPUT] dataset

Quick reference examples
------------------------

.. code-block:: console

   $ dptools train /path/to/dataset # simple single model
   $ dptools train -e /path/to/dataset # ensemble (4) of models
   $ dptools train -e -s /path/to/dataset # submit 4 slurm jobs to train ensemble
   $ dptools train -p /path/to/training/dir /path/to/dataset # specify dir to train in
   $ dptools train -i /path/to/in.json /path/to/dataset # specify in.json parameter file


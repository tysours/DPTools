=====
input
=====

The ``dptools input`` command is used to create deepmd-kit datasets to train a model
from DFT (or some other *ab-initio* method) calculations.

General usage,

.. code-block:: console

   $ dptools input [-h] [-n N] [-p PATH] [-a] input_file [input_file ...]

.. code-block:: bash

   positional arguments:
     input_file            .db, .traj, or vasprun.xml files
   
   optional arguments:
     -h, --help            show this help message and exit
     -n N                  Max number of images to take from each db (default: None)
     -p PATH, --path PATH  Specify path to dataset directory (default: ./data)
     -a, --append          Append to dataset if system already exists in dataset directory (default: False)
   

Quick reference examples
------------------------

.. code-block:: console

   $ dptools input 00_system1.db 00_system2.db
   $ dptools input 0*_sys*.db # equivalent to above
   $ dptools input 00_system1/vasprun.xml 00_system2/vasprun.xml
   $ dptools input -p /path/to/dataset/folder 0*.db
   $ dptools input -a -p /path/to/dataset/folder 0*.db


Create dataset from VASP/ASE results
------------------------------------

The following file types are supported by ``dptools input``:

.. list-table::

   * - ``.xml``
     - ``.traj``
     - ``.db``

First, each unique system (defined as having identical number of atoms and identical
indexing for all images) should be given saved as a separate file and given a unique and
descriptive name (e.g., iter0_SOD_5H2O.db). The deepmd dataset can then be created with,

.. code-block:: console

   $ dptools input /path/to/DFT_data/*.db

.. note::

   If vasprun.xml files from DFT-MD calculations are used, place the vasprun.xml in a
   separate folder with the name of the system.

This will create training (80%), validation (10%), and testing (10%) datasets in your current
directory in a folder named data by default. 


.. warning::

   By default, training sets are overwritten if an input has the same name as an existing
   system in the dataset folder. To append new images to existing datasets, include the ``-a``
   or ``--append`` flag when running the command. Note that it is generally a good idea to
   create a new system name each time you add more data when training iteratively (e.g.,
   iter1_system1.db, iter2_system1.db). This allows for easy comparison of different iteration
   datasets when making parity plots.

You can also specify the location of the dataset folder with ``-p`` or ``--path`` if you do
not wish to create the dataset in ``./data``. E.g.,

.. code-block:: console

   $ dptools input -p /path/to/dataset_directory *.db


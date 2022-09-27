============
Installation
============

DeePMD-kit with LAMMPS
======================

DPTools requires and assumes that DeePMD-kit_ with the LAMMPS_ package has already been installed.

.. important::
    Ensure that your installation of DeePMD-kit includes LAMMPS built with the DEEPMD package! 
    A simple :code:`pip install deepmd-kit` is **NOT** sufficient, as LAMMPS will not be installed or configured properly.

Full details can be found at the `official DeePMD-kit's documentation
<https://docs.deepmodeling.com/projects/deepmd/en/master/install/index.html>`_.

In short, the most straightforward way to accomplish this is by using conda,

.. code-block:: console

    $ conda create -n deepmd deepmd-kit=*=*cpu libdeepmd=*=*cpu lammps -c https://conda.deepmodeling.com -c defaults
    $ conda activate deepmd

Or alternatively by downloading and installing the `latest offline package
<https://github.com/deepmodeling/deepmd-kit/releases>`_ from DeePMD-kit's GitHub,

.. code-block:: console

    $ cd /path/to/install
    $ wget https://github.com/deepmodeling/deepmd-kit/releases/download/v2.1.5/deepmd-kit-2.1.5-cpu-Linux-x86_64.sh
    $ sh deepmd-kit-2.1.5-cpu-Linux-x86_64.sh

Accept the license and installation path, and then the resulting directory can be activated as a conda environment,

.. code-block:: console

    $ conda activate /path/to/install/deepmd-kit

DPTools
=======

Install with pip
----------------

.. note::
   Make sure to activate your deepmd-kit environment before installing DPTools!

The latest stable version (1.0.1) of DPTools can be installed via the ``pip`` command,

.. code-block:: console

   $ pip install dpmdtools

Install from source
-------------------

The latest developer version can be installed by cloning the GitHub repo,

.. code-block:: console

   $ cd /path/to/install
   $ git clone https://github.com/tysours/DPTools.git

Then simply use pip while inside the project folder,

.. code-block:: console

   $ cd DPTools
   $ pip install .


Verify your installation was a success using the command,

.. code-block:: console

   $ dptools --version

If the above command prints the current version with no errors, you are ready to use DPTools!

.. _DeePMD-kit: https://github.com/deepmodeling/deepmd-kit
.. _LAMMPS: https://lammps.org

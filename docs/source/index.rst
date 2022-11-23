.. DPTools documentation master file, created by
   sphinx-quickstart on Thu Sep 15 05:26:37 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to DPTools's documentation!
===================================

**D**\eep **P**\otential **Tools** (DPTools) provides a command-line interface and python library
to simplify training and deploying DeePMD-kit_ machine learning potentials (MLPs), also known as
ML force fields. The primary goal of DPTools is to condense workflows for training DP MLPs and
running atomistic simulations with LAMMPS_ on HPC systems into a handful of intuitive CLI commands.
It is intended for scientists with knowledge of quantum mechanics-based *ab-initio* simulation
methods who are interested in effortlessly transitioning to ML-based approaches to greatly
increase computational throughput. It requires no prior experience with DeePMD-kit or LAMMPS
software, only familiarity with the popular ASE_ python package is needed.

.. toctree::
   :maxdepth: 3
   :caption: Getting Started

   installation

.. toctree::
   :maxdepth: 3
   :caption: Usage

   commands/index
   tutorials/index
   faq/index

.. toctree::
   :maxdepth: 5
   :caption: Source

   api/api
   DPTools GitHub <https://github.com/tysours/DPTools>
   Reporting Issues <https://github.com/tysours/DPTools/issues>

.. _DeePMD-kit: https://github.com/deepmodeling/deepmd-kit
.. _LAMMPS: https://lammps.org
.. _ASE: https://wiki.fysik.dtu.dk/ase/index.html

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

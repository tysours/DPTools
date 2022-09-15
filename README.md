# DPTools
**D**eep **P**otential **Tools** (DPTools) provides a command-line interface and python library to simplify training and deploying [DeePMD-kit](https://github.com/deepmodeling/deepmd-kit) machine learning potentials (MLPs), also known as ML force fields. The primary goal of DPTools is to condense workflows for training DP MLPs and running atomistic simulations with [LAMMPS](https://www.lammps.org)  on HPC systems into a handful of intuitive CLI commands. It is intended for scientists with knowledge of quantum mechanics-based *ab-initio* simulation methods who are interested in effortlessly transitioning to ML-based approaches to greatly increase computational throughput. It requires no prior experience with DeePMD-kit or LAMMPS software, only familiarity with the popular [Atomic Simulation Environment (ASE)](https://wiki.fysik.dtu.dk/ase/index.html) python package is needed.

## Main Features

* Setup deepmd-kit training sets from VASP output or common ASE formats
* Train ensemble of DP models
* Generate parity plots to assess accuracy of MLP energy and force predictions
* Intelligently sample and select new training configurations from DPMD trajectories
* Easily setup and run different atomistic simulations in LAMMPS:
	* Single point energy calculations
	* Structure geometry optimizations
	* Structure unit cell optimizations
	* Molecular dynamics using the NVT ensemble
	* Molecular dynamics using the NPT ensemble
	* Equations of State fits and bulk moduli calculations
	* Predict vibratrional properties using the finite difference approach
	* Other common simulation methods available upon request
* Supports Slurm job submission on HPC systems
* Setup and run simulations on thousands of structures with a single command

## Documentation
For detailed descriptions on setting up and using DPTools, visit the [official documentation](https://dptools.readthedocs.io).

## Installation
The current stable version (0.2.2) of DPTools can be installed using `pip` with the following command:

~~~
pip install dpmdtools
~~~

To verify that the installation was completed successfully, run the command:

~~~
dptools --version
~~~

## Support
If you are having issues with DPTools, create an issue [here](https://github.com/tysours/DPTools/issues). For more assistance, new feature requests, or general inquiries, feel free to contact Ty at tsours@ucdavis.edu.

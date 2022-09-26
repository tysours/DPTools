=======
convert
=======

The ``dptools convert`` command is used to conveniently convert between different structure 
file types and concatenate multiple input files into a single output file. It is generally
used as a convenient tool for setting up DFT calculation results to be used with the
:doc:`input` command.

General usage,

.. code-block:: console

   $ dptools convert [-h] [-i INDICES] input [input ...] output

Quick reference examples
------------------------

.. code-block:: console

   $ dptools convert thing.cif thing.traj
   $ dptools convert md_000/vasprun.xml md_001/vasprun.xml full_md.traj
   $ dptools convert md_???/vasprun.xml full_md.traj # equivalent to above
   $ dptools convert 0*/vasp_spe.traj all_spe.traj
   $ dptools convert -i ::10 vasprun.xml condensed_traj.traj

Simple file type conversion
---------------------------

The simplest usage of ``dptools convert`` is to convert from one structural file type
to another. Such as converting the file ``atoms.cif`` to ``atoms.xyz``,

.. code-block:: console

   $ dptools convert atoms.cif atoms.xyz

Concatenate MD trajectories
---------------------------

The ``convert`` command can also be used to concatenate separate MD trajectories into
a single trajectory (especially useful if running variable time AIMD jobs that start and
restart in a new directory). The final image in each input is compared with the first image
of the previous input to ensure that only unique images are written.

If for example you have multiple vasprun.xml files from a single variable-time MD run located in
``md_000``, ``md_001``, ..., ``md_xxx`` folders, you can concatenate them all into a single
trajectory using this command (make sure to take advantage of
`Bash wildcards <https://www.shell-tips.com/bash/wildcards-globbing/#gsc.tab=0>`_
when using the command line!),

.. code-block:: console

   $ dptools convert md_???/vasprun.xml iteration0_system1.db

Note the unique name given to the output file. Naming outputs in this way makes it trivial to
then setup a training set for deepmd-kit with :doc:`input`.

Concatenate single point energy calculations
--------------------------------------------

Similar to the previous example, ``convert`` can be used to concatenate multiple single point
energy calculations into a single file. This is useful if running single points from DPMD
trajectories in separate directories to get more DFT data for training a new model iteration.

.. code-block:: console

   $ dptools convert 0*/vasp_spe.traj iteration1_system1.db

Again, notice the unique name assigned to the output!

Condense long MD run
--------------------

If you have a long MD run that you want to condense by taking every 100th image, just include the
appropriate index slice with the ``-i`` flag,

.. code-block:: console

   $ dptools convert -i ::100 vasprun.xml condensed_run.traj

.. note::
    
   It is usually a good idea to condense long MD runs to avoid redundant data points in your
   training sets. Training on every image of a 1,000,000 step MD run is inefficient! You could get
   comparable results training on every 100th image without taking up tons of space on your
   hard drive.

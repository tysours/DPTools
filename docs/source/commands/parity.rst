======
parity
======

General usage,

.. code-block:: console

   $ dptools parity [-h] [-m MODEL] [-l {mse,mae,rmse}] [--xyz] [--fancy] [system ...]


Quick reference examples
------------------------

.. code-block:: console

   $ dptools parity
   $ dptools parity /path/to/dataset/system*/test/set*
   $ dptools parity -m ../old_graph.pb test_set.traj
   $ dptools parity -l mae
   $ dptools parity -l mae --fancy --xyz

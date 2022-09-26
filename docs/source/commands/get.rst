
===
get
===

The get command is used to retrieve parameter files (params.yaml) to run customizable simulations.

General usage,

.. code-block:: console

   $ dptools get [-h] calculation

Quick reference examples
------------------------

.. code-block::

   $ dptools get cellopt
   $ dptools get nvt-md
   $ dptools get nvt-md.900K # custom simulation params
   $ dptools get in.json # get training param file

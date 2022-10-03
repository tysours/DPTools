
===
get
===

The get command is used to retrieve simulation parameter files (params.yaml) to run
customizable simulations. It can also be used to retrieve the current default deepmd-kit
training parameter file (in.json).

General usage,

.. code-block:: console

   $ dptools get [-h] simulation

Quick reference examples
------------------------

.. code-block:: console

   $ dptools get cellopt
   $ dptools get list
   $ dptools get nvt-md
   $ dptools get nvt-md.900K # custom simulation params
   $ dptools get in.json # get training param file

View available simulation types
-------------------------------

To get a list of the saved (custom and default) simulation types, just pass
``list`` as the simulation argument,

.. code-block:: console

   $ dptools get list

Get simulation parameters
-------------------------

To retrieve the parameters (params.yaml file) for any simulation, enter the simulation keyword
as the simulation argument,

.. code-block:: console

   $ dptools get nvt-md

You can then edit params.yaml to your liking and then :doc:`run the simulation <run>` or
:ref:`save the new parameters for future use<mod_params>`.

Get training parameters
-----------------------

You can also use the ``get`` command to retrieve the current default deepmd-kit training
parameter file (in.json),

.. code-block:: console

   $ dptools get in.json

Note that you can also edit the in.json file to your liking and :ref:`save it as your new default
training parameters<set_training>`.

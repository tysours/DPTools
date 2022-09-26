=====
input
=====

General usage,

.. code-block:: console

   $ dptools input [-h] [-n N] [-p PATH] [-a] input [input ...]

Quick reference examples
------------------------

.. code-block:: console

   $ dptools input 00_system1.db 00_system2.db
   $ dptools input 0*_sys*.db # equivalent to above
   $ dptools input 00_system1/vasprun.xml 00_system2/vasprun.xml
   $ dptools input -p /path/to/dataset/folder 0*.db
   $ dptools input -a -p /path/to/dataset/folder 0*.db

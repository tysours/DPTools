#!/usr/bin/env bash
#dptools run spe CHA.cif # should fail if no model set

# set model
#dptools set zeolites.pb

# show info on set model
#dptools info

# set sbatch settings for job submission
#dptools set slurm.sh

#dptools run cellopt CHA.cif

dptools run -g opt ???/???.cif

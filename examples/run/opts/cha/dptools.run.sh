#!/usr/bin/env bash
#SBATCH --time=1:00:00 --nodes=1 --partition=med --ntasks-per-node=1 -c 1 --output=job.out --error=job.err
export OMP_NUM_THREADS=1
export TF_INTRA_OP_PARALLELISM_THREADS=1
export TF_INTER_OP_PARALLELISM_THREADS=1

dptools run -o opt.traj opt CHA.cif
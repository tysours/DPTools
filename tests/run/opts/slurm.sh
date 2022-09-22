just a test for setting slurm settings
#SBATCH --time=1:00:00 --nodes=1 --partition=med --ntasks-per-node=1 -c 1
#SBATCH --output=job.out
#SBATCH --error=job.err

export OMP_NUM_THREADS=1
export TF_INTRA_OP_PARALLELISM_THREADS=1
no other text matters besides sbatch comments and env vars
export TF_INTER_OP_PARALLELISM_THREADS=1

boooooooooooo
ahhhhhhh

whoaaaa

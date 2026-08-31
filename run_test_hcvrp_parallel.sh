#!/bin/bash
#SBATCH --job-name=parco_hcvrp_parallel_test
#SBATCH --output=hcvrp_parallel_test.log
#SBATCH --error=hcvrp_parallel_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:3

source .venv/bin/activate

srun python test.py \
  --problem hcvrp \
  --checkpoint checkpoints/hcvrp/parco.ckpt \
  --decode_type greedy \
  --batch_size 128 \

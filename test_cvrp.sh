#!/bin/bash
#SBATCH --job-name=parco_cvrp_test
#SBATCH --output=cvrp_parco_test.log
#SBATCH --error=cvrp_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

# Checkpoint of the CVRP training run
RUN_GROUP=cvrp_n100_m7
RUN_NAME=parco_cvrp
CKPT=$(ls -td logs/train/runs/${RUN_GROUP}/${RUN_NAME}/*/checkpoints/last.ckpt | head -n 1)
echo "Using checkpoint: ${CKPT}"

# Evaluates every dataset under data/cvrp/, i.e. N in {50, 100, 200} x M in {3, 5, 7}.
# N=200 is beyond the training range, so those rows are zero-shot generalisation.
srun python test.py \
  --problem cvrp \
  --checkpoint "${CKPT}" \
  --decode_type greedy \
  --batch_size 128

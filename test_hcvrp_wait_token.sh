#!/bin/bash
#SBATCH --job-name=parco_hcvrp_wait_token_test
#SBATCH --output=hcvrp_wait_token_parco_test.log
#SBATCH --error=hcvrp_wait_token_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Checkpoint of the wait-token training run
RUN_GROUP=hcvrp_n100_m7
RUN_NAME=parco_wait_token
CKPT=$(ls -td logs/train/runs/${RUN_GROUP}/${RUN_NAME}/*/checkpoints/last.ckpt | head -n 1)
echo "Using checkpoint: ${CKPT}"

srun python test.py \
  --problem hcvrp \
  --checkpoint "${CKPT}" \
  --decode_type greedy \
  --batch_size 128

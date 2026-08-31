#!/bin/bash
#SBATCH --job-name=parco_hcvrp_tanh_scaled_test
#SBATCH --output=hcvrp_tanh_scaled_parco_test.log
#SBATCH --error=hcvrp_tanh_scaled_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# Run directory of the training job, i.e.
#   logs/train/runs/<wandb.group>/<wandb.name>/<timestamp>/checkpoints/last.ckpt
# The name encodes the clipping setting; change it if you swept C or the mode.
RUN_GROUP=hcvrp_n100_m7
RUN_NAME=parco_tanh_scaled_c10_attn_scaled_c10

# Pick the most recent timestamped run for that setting
CKPT=$(ls -td logs/train/runs/${RUN_GROUP}/${RUN_NAME}/*/checkpoints/last.ckpt | head -n 1)
echo "Using checkpoint: ${CKPT}"

srun python test.py \
  --problem hcvrp \
  --checkpoint "${CKPT}" \
  --decode_type greedy \
  --batch_size 128

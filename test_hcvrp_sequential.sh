#!/bin/bash
#SBATCH --job-name=parco_hcvrp_sequential_test
#SBATCH --output=hcvrp_sequential_parco_test.log
#SBATCH --error=hcvrp_sequential_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

# Checkpoint of the sequential training run
RUN_GROUP=hcvrp_n100_m7
RUN_NAME=parco_sequential
SEQ_CKPT=$(ls -td logs/train/runs/${RUN_GROUP}/${RUN_NAME}/*/checkpoints/last.ckpt | head -n 1)



echo "sequential checkpoint: ${SEQ_CKPT}"


# test.py already reports, per dataset: average cost, per-step inference time,
# total inference time and average decoding steps -- i.e. both axes of the ablation.

echo "=========================================================="
echo "[A] sequential model, sequential decoding (this branch)"
echo "=========================================================="
srun python test.py \
  --problem hcvrp \
  --checkpoint "${SEQ_CKPT}" \
  --decode_type sequential_greedy \
  --batch_size 128


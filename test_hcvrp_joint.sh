#!/bin/bash
#SBATCH --job-name=parco_hcvrp_joint_test
#SBATCH --output=hcvrp_joint_parco_test.log
#SBATCH --error=hcvrp_joint_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

RUN_GROUP=hcvrp_n100_m7
RUN_NAME=parco_joint
CKPT=$(ls -td logs/train/runs/${RUN_GROUP}/${RUN_NAME}/*/checkpoints/last.ckpt | head -n 1)
echo "Using checkpoint: ${CKPT}"

# test.py reports average cost, per-step time, total time and average decoding
# steps -- the step count should match parallel PARCO, not the sequential run.
echo "=========================================================="
echo "[A] joint-trained model, joint decoding"
echo "=========================================================="
srun python test.py \
  --problem hcvrp \
  --checkpoint "${CKPT}" \
  --decode_type joint_greedy \
  --batch_size 128




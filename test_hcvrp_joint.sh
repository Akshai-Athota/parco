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

# Zero-shot cell: does collision-free decoding help a model trained the normal
# way? Separates "joint decoding helps" from "training jointly helps".
# Point PAR_CKPT at the checkpoint behind your reproduced baseline numbers.
PAR_CKPT=$(ls -td logs/train/runs/${RUN_GROUP}/parco/*/checkpoints/last.ckpt | head -n 1)
echo "=========================================================="
echo "[B] parallel-trained model, joint decoding (zero-shot)"
echo "=========================================================="
srun python test.py \
  --problem hcvrp \
  --checkpoint "${PAR_CKPT}" \
  --decode_type joint_greedy \
  --batch_size 128

#!/bin/bash
#SBATCH --job-name=parco_hcvrp_k7_test
#SBATCH --output=hcvrp_k7_parco_test.log
#SBATCH --error=hcvrp_k7_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Evaluate the k = 7 model at k = 7 (masked joint).
# All 12 HCVRP test sets, greedy decoding, 1,280 instances each.

CKPT=$(ls -td logs/train/runs/hcvrp_n100_m7/parco_k7/*/checkpoints/last.ckpt 2>/dev/null | head -n 1)
if [ -z "${CKPT}" ]; then
  echo "No checkpoint for k = 7. Run train_hcvrp_k7.sh first."
  exit 1
fi
echo "k = 7   checkpoint: ${CKPT}"

srun python test.py \
  --problem hcvrp \
  --checkpoint "${CKPT}" \
  --decode_type kparallel_greedy \
  --decode_k 7 \
  --batch_size 128

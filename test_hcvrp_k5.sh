#!/bin/bash
#SBATCH --job-name=parco_hcvrp_k5_test
#SBATCH --output=hcvrp_k5_parco_test.log
#SBATCH --error=hcvrp_k5_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Evaluate the k = 5 model at k = 5 (interior point of the Pareto front).
# All 12 HCVRP test sets, greedy decoding, 1,280 instances each.

CKPT=$(ls -td logs/train/runs/hcvrp_n100_m7/parco_k5/*/checkpoints/last.ckpt 2>/dev/null | head -n 1)
if [ -z "${CKPT}" ]; then
  echo "No checkpoint for k = 5. Run train_hcvrp_k5.sh first."
  exit 1
fi
echo "k = 5   checkpoint: ${CKPT}"

srun python test.py \
  --problem hcvrp \
  --checkpoint "${CKPT}" \
  --decode_type kparallel_greedy \
  --decode_k 5 \
  --batch_size 128

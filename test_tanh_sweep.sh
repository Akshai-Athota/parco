#!/bin/bash
#SBATCH --job-name=tanh_sweep_test
#SBATCH --output=tanh_sweep_test.log
#SBATCH --error=tanh_sweep_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Evaluate every tanh arm that has finished training. Greedy decoding, all 12
# HCVRP test sets. Arms still running are skipped with a message.
#
# The clipping form is applied at inference too, but note it cannot change a
# greedy argmax for fixed weights (both forms are strictly increasing), so any
# difference you see here is a TRAINING effect.

for RUN in $(ls -d logs/train/runs/hcvrp_n100_m7/parco_tanh_* 2>/dev/null); do
  NAME=$(basename "${RUN}")
  CKPT=$(ls -td "${RUN}"/*/checkpoints/last.ckpt 2>/dev/null | head -n 1)
  if [ -z "${CKPT}" ]; then
    echo "[run] ${NAME}  -- no checkpoint yet, skipping"
    continue
  fi
  echo "=========================================================="
  echo "[run] ${NAME}"
  echo "checkpoint: ${CKPT}"
  echo "=========================================================="
  srun python test.py \
    --problem hcvrp \
    --checkpoint "${CKPT}" \
    --decode_type greedy \
    --batch_size 128
done

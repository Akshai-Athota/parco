#!/bin/bash
#SBATCH --job-name=parco_hcvrp_k_trained_test
#SBATCH --output=hcvrp_k_trained_test.log
#SBATCH --error=hcvrp_k_trained_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Each k-trained model evaluated at the k it was trained with. Compare this
# against test_hcvrp_k_sweep.sh (one model, every k) to separate
#   "decoding at k helps"  from  "training at k helps".

for K in 1 2 3 4 5 6 7; do
  CKPT=$(ls -td logs/train/runs/hcvrp_n100_m7/parco_k${K}/*/checkpoints/last.ckpt 2>/dev/null | head -n 1)
  if [ -z "${CKPT}" ]; then
    echo "[k = ${K}] no checkpoint found, skipping"
    continue
  fi
  echo "=========================================================="
  echo "[k = ${K}] trained and evaluated at k = ${K}"
  echo "checkpoint: ${CKPT}"
  echo "=========================================================="
  srun python test.py     --problem hcvrp     --checkpoint "${CKPT}"     --decode_type kparallel_greedy     --decode_k ${K}     --batch_size 128
done

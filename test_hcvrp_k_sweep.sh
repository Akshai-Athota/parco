#!/bin/bash
#SBATCH --job-name=parco_hcvrp_k_sweep
#SBATCH --output=hcvrp_k_sweep_test.log
#SBATCH --error=hcvrp_k_sweep_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# ============================================================================
# THE PARETO FRONT FROM A SINGLE CHECKPOINT - NO TRAINING REQUIRED.
#
# k is a decoding parameter, so one trained model can be evaluated at every k.
# This produces the cost-vs-steps front in minutes rather than days.
#
# Point CKPT at any checkpoint you already have: the parallel baseline, the
# sequential model, or a k-trained one. Running it on the PARALLEL baseline is
# the cleanest reading of "what does the decoding rule alone buy?", since the
# weights are then held fixed across the whole sweep.
# ============================================================================

CKPT=${CKPT:-$(ls -td logs/train/runs/hcvrp_n100_m7/parco/*/checkpoints/last.ckpt 2>/dev/null | head -n 1)}
echo "checkpoint: ${CKPT}"

for K in 1 2 3 4 5 7; do
  echo "=========================================================="
  echo "[k = ${K}]  $( [ "${K}" = "1" ] && echo '= full sequential' || ([ "${K}" = "7" ] && echo '= masked joint' || echo 'interior point') )"
  echo "=========================================================="
  srun python test.py     --problem hcvrp     --checkpoint "${CKPT}"     --decode_type kparallel_greedy     --decode_k ${K}     --batch_size 128
done

# Read "Average cost" and "Average eval steps" from the log for each k and plot
# cost against steps: that is the Pareto front.

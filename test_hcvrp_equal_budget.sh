#!/bin/bash
#SBATCH --job-name=parco_hcvrp_equal_budget
#SBATCH --output=hcvrp_equal_budget.log
#SBATCH --error=hcvrp_equal_budget.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1

source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# ---------------------------------------------------------------------------
# Equal-budget comparison: parallel PARCO vs the k-parallel models.
#
# The greedy table shows k=1 beating parallel PARCO by 4.6%, but a greedy k=1
# rollout costs ~85 decoder passes against PARCO's ~66. This run removes that
# confound by giving every model the same inference budget, measured in decoder
# passes per instance, and letting it spend the budget on best-of-n sampling.
#
# No training is needed: this reuses the five checkpoints already trained with
# the identical 6-GPU recipe (the tanh control = stock parallel PARCO, plus
# k = 1, 2, 4, 7). That is why there is no matching train_*.sh for this one.
#
# Sample counts are dense at the low end because the budget crossover sits
# between 1x and 4x, which is the region that decides the comparison.
# ---------------------------------------------------------------------------

srun python scripts/equal_budget_eval.py \
  --problem hcvrp \
  --samples 2 3 4 6 8 12 16 24 32 \
  --budgets 1.0 1.3 2.0 3.0 4.0 6.0 8.0 16.0 32.0 \
  --reference parallel \
  --instances_per_batch 16 \
  --out equal_budget_results.csv

echo
echo "=========================================================="
echo "Done. Per-point data in equal_budget_results.csv"
echo "The matched-budget table is printed at the end of the log."
echo "=========================================================="

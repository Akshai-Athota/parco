#!/bin/bash
#SBATCH --job-name=parco_hcvrp_k7
#SBATCH --output=hcvrp_k7_parco.log
#SBATCH --error=hcvrp_k7_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# ---------------------------------------------------------------------------
# k-parallel decoding, k = 7
#   masked joint: every agent assigned from a single decoder pass
#
# Per decoder pass, k pairs are drawn from ONE joint log-softmax over the
# flattened M x (M+N) logits; after each pick that agent's ROW and that node's
# COLUMN are masked, so no two agents can be given the same node. Agents not
# reached in the pass repeat their current node (a no-op in the env).
#
#   k = 1  -> idea 1 (full sequential)      slowest, most accurate
#   k = 7  -> idea 3 (masked joint)         fastest, parallel-length episodes
#
# Only model.policy.decode_k differs between these scripts. Everything else
# matches the other runs, so the front is measured under one recipe.
# Run dir: logs/train/runs/hcvrp_n100_m7/parco_k7/<timestamp>/
# ---------------------------------------------------------------------------
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_k \
    model.policy.decode_k=7 \
    logger.wandb.offline=True \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=8

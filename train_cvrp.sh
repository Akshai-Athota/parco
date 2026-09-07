#!/bin/bash
#SBATCH --job-name=parco_cvrp
#SBATCH --output=cvrp_parco.log
#SBATCH --error=cvrp_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# Min-max CVRP with a homogeneous fleet (cap_m = 50 for every vehicle, unit speed).
# Zero model changes vs HCVRP: only the environment and its generator are new,
# so cost and runtime here are directly comparable to the HCVRP baseline.
#
# PREREQUISITE: the validation/test sets are generated locally, not downloaded.
# Run this once from the repo root before submitting (a few minutes, CPU only):
#     python scripts/generate_cvrp_data.py

srun python train.py experiment=cvrp \
    logger.wandb.offline=True \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=8

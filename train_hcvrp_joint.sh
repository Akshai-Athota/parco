#!/bin/bash
#SBATCH --job-name=parco_hcvrp_joint
#SBATCH --output=hcvrp_joint_parco.log
#SBATCH --error=hcvrp_joint_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# Masked joint decoding: one decoder pass per environment step (same as parallel
# PARCO), but agents are assigned one at a time from the flattened joint
# distribution with each chosen node masked out, so collisions cannot happen and
# the scored action is always the executed action.
#
# Episodes are the same length as parallel PARCO, so batch/accumulation are kept
# identical to the baseline run -- that keeps the wall-clock comparison honest.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_joint \
    logger.wandb.offline=True \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=8

#!/bin/bash
#SBATCH --job-name=parco_hcvrp_sequential
#SBATCH --output=hcvrp_sequential_parco.log
#SBATCH --error=hcvrp_sequential_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:8


source .venv/bin/activate

# Full sequential (autoregressive) decoding: one (agent, node) pair committed per
# environment step, decoder re-run on the updated state before the next pick.
#
# WARNING: construction needs sum_m T_m steps instead of max_m T_m, so an epoch is
# roughly M times slower than `experiment=hcvrp` (M = 3..7 during training). If the
# 100-epoch run does not fit in the queue's walltime, drop trainer.max_epochs and
# re-run the PARCO baseline for the SAME number of epochs, otherwise the cost
# comparison is confounded by training budget.

srun python train.py experiment=hcvrp_sequential \
    logger.wandb.offline=True \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=7 \
    +trainer.accumulate_grad_batches=8

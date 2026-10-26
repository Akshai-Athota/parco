#!/bin/bash
#SBATCH --job-name=tanh_c_scaled_lr3e-4
#SBATCH --output=tanh_c_scaled_lr3e-4.log
#SBATCH --error=tanh_c_scaled_lr3e-4.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# ---------------------------------------------------------------------------
# Scaled form, decoder only, 3x lr.
# The gain argument predicts the scaled form needs ~C times the lr.
#
#   phi(z) = g * tanh(z / tau)     gain at origin = g/tau,  knee ~ 2*tau
#   here:   mode=scaled  g=10  tau=1  ->  gain 1
#   encoder attention clipping: off
#   learning rate: 3e-4
#
# All arms use 6 GPUs so the effective batch is 768 throughout -- the earlier
# tanh run used 8 GPUs and was therefore not comparable to the other ideas.
# Run dir: logs/train/runs/hcvrp_n100_m7/parco_tanh_scaled_g10_t1_attn0_lr3e-4/
# ---------------------------------------------------------------------------
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_tanh_lr \
    model.policy.tanh_clip_mode=scaled \
    model.policy.tanh_clipping=10 \
    model.policy.tanh_clip_tau=1 \
    model.policy.attn_tanh_clipping=0 \
    model.optimizer_kwargs.lr=3e-4 \
    logger.wandb.offline=True \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=8

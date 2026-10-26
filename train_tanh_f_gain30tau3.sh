#!/bin/bash
#SBATCH --job-name=tanh_f_gain30tau3
#SBATCH --output=tanh_f_gain30tau3.log
#SBATCH --error=tanh_f_gain30tau3.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# ---------------------------------------------------------------------------
# Gain-matched: 30*tanh(z/3) keeps PARCO's gain of 10 but moves the
# saturation knee from ~2 to ~6. This is the ONLY arm that tests the
# original hypothesis -- later saturation -- without also changing the gain.
#
#   phi(z) = g * tanh(z / tau)     gain at origin = g/tau,  knee ~ 2*tau
#   here:   mode=general  g=30  tau=3  ->  gain 10
#   encoder attention clipping: off
#   learning rate: 1e-4
#
# All arms use 6 GPUs so the effective batch is 768 throughout -- the earlier
# tanh run used 8 GPUs and was therefore not comparable to the other ideas.
# Run dir: logs/train/runs/hcvrp_n100_m7/parco_tanh_general_g30_t3_attn0_lr1e-4/
# ---------------------------------------------------------------------------
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_tanh_lr \
    model.policy.tanh_clip_mode=general \
    model.policy.tanh_clipping=30 \
    model.policy.tanh_clip_tau=3 \
    model.policy.attn_tanh_clipping=0 \
    model.optimizer_kwargs.lr=1e-4 \
    logger.wandb.offline=True \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=8

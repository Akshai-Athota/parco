#!/bin/bash
#SBATCH --job-name=tanh_a_ctrl_fixed
#SBATCH --output=tanh_a_ctrl_fixed.log
#SBATCH --error=tanh_a_ctrl_fixed.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# ---------------------------------------------------------------------------
# CONTROL. PARCO's own clipping, decoder only, base lr, on 6 GPUs.
# Every other arm is compared against THIS, not against the earlier 8-GPU run,
# so the effective-batch difference is removed from the comparison.
#
#   phi(z) = g * tanh(z / tau)     gain at origin = g/tau,  knee ~ 2*tau
#   here:   mode=fixed  g=10  tau=1  ->  gain 10
#   encoder attention clipping: off
#   learning rate: 1e-4
#
# All arms use 6 GPUs so the effective batch is 768 throughout -- the earlier
# tanh run used 8 GPUs and was therefore not comparable to the other ideas.
# Run dir: logs/train/runs/hcvrp_n100_m7/parco_tanh_fixed_g10_t1_attn0_lr1e-4/
# ---------------------------------------------------------------------------
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_tanh_lr \
    model.policy.tanh_clip_mode=fixed \
    model.policy.tanh_clipping=10 \
    model.policy.tanh_clip_tau=1 \
    model.policy.attn_tanh_clipping=0 \
    model.optimizer_kwargs.lr=1e-4 \
    logger.wandb.offline=True \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=8

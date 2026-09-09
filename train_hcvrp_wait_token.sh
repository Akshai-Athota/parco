#!/bin/bash
#SBATCH --job-name=parco_hcvrp_wait_token
#SBATCH --output=hcvrp_wait_token_parco.log
#SBATCH --error=hcvrp_wait_token_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# Explicit idle action: the action space grows from N to N+1 with a learned,
# always-available wait token, so agents can proactively stay put instead of
# idling only when the conflict handler overrules them.
#
# MEMORY: the previous attempt at this idea died with CUDA OOM. The cause is that
# an unmasked wait lets every agent idle at once, which leaves the state
# unchanged, so the decoder returns identical logits and the loop never
# terminates -- memory then blows up on the accumulated per-step tensors. The
# decoding strategy now forces one agent to act whenever an instance would stall,
# and policy.max_steps=1000 caps any residual runaway. On top of that we halve
# the per-step batch and double gradient accumulation, keeping the effective
# batch at 128 while roughly halving activation memory.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_wait_token \
    logger.wandb.offline=True \
    model.batch_size=8 \
    model.val_batch_size=8 \
    model.test_batch_size=8 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=16

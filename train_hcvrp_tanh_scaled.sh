#!/bin/bash
#SBATCH --job-name=parco_hcvrp_tanh_scaled
#SBATCH --output=hcvrp_tanh_scaled_parco.log
#SBATCH --error=hcvrp_tanh_scaled_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:8


source .venv/bin/activate

# Scaled tanh clipping  C * tanh(z / C)  on BOTH the decoder logits and the
# encoder MHA attention logits, with C = 10.
#
# To sweep C, change the two `*tanh_clipping` values below (5 / 10 / 20) and the
# three #SBATCH names at the top. To run the fixed form C * tanh(z) as a control,
# set both `*tanh_clip_mode` to "fixed". To turn the encoder-attention half off
# entirely (decoder-only study), set model.policy.attn_tanh_clipping=0.
# The run directory is derived from these values, so runs never collide.

srun python train.py experiment=hcvrp_tanh_scaled \
    model.policy.tanh_clipping=10 \
    model.policy.tanh_clip_mode=scaled \
    model.policy.attn_tanh_clipping=10 \
    model.policy.attn_tanh_clip_mode=scaled \
    model.batch_size=16 \
    model.val_batch_size=16 \
    model.test_batch_size=16 \
    model.num_augment=4 \
    +model.dataloader_num_workers=7 \
    +trainer.accumulate_grad_batches=8

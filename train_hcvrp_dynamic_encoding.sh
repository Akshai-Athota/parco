#!/bin/bash
#SBATCH --job-name=parco_hcvrp_dyn_enc
#SBATCH --output=hcvrp_dynamic_encoding_parco.log
#SBATCH --error=hcvrp_dynamic_encoding_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# Dynamic re-encoding: the encoder runs again on the CURRENT state after every
# committed (vehicle, node) pair, using HCVRPDynamicInitEmbedding so the new pass
# actually sees updated positions, remaining capacities and served customers.
#
# COST WARNING. The encoder is 3 transformer layers over M+N tokens and now runs
# ~N times per instance instead of once, all inside the autograd graph. This is
# far heavier than any previous run (sequential decoding alone already took 29 h
# for 100 epochs). The per-step batch is therefore 4 with 32-step accumulation,
# which keeps the effective batch at 768 as in the other runs.
#
# If a 100-epoch run will not fit in the 72 h job limit, the options are:
#   trainer.max_epochs=30                      (and re-run the baseline at 30)
#   model.policy.reencode_every=4              (re-encode every 4th step)
#   model.batch_size=2 +trainer.accumulate_grad_batches=64   (if it OOMs)
# Training can also be resumed across jobs with ckpt_path=<path to last.ckpt>.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_dynamic_encoding \
    logger.wandb.offline=True \
    model.batch_size=4 \
    model.val_batch_size=4 \
    model.test_batch_size=4 \
    model.num_augment=4 \
    +model.dataloader_num_workers=5 \
    +trainer.accumulate_grad_batches=32

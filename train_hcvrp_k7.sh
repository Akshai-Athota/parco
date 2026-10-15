#!/bin/bash
#SBATCH --job-name=parco_hcvrp_k7
#SBATCH --output=hcvrp_k7_parco.log
#SBATCH --error=hcvrp_k7_parco.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:6


source .venv/bin/activate

# k-parallel decoding with k = 7: all agents per pass, identical to masked joint decoding
#
#   k = 1  full sequential (idea 1)   - slowest, most accurate
#   k = 7  masked joint   (idea 3)    - fastest, parallel-length episodes
#
# Only model.policy.decode_k differs between these scripts; everything else
# matches the other runs so the Pareto front is measured under one recipe.
# The run directory is named parco_k7, so the k values never collide.
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

srun python train.py experiment=hcvrp_k     model.policy.decode_k=7     logger.wandb.offline=True     model.batch_size=16     model.val_batch_size=16     model.test_batch_size=16     model.num_augment=4     +model.dataloader_num_workers=5     +trainer.accumulate_grad_batches=8

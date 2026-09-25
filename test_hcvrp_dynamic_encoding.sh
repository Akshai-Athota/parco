#!/bin/bash
#SBATCH --job-name=parco_hcvrp_dyn_enc_test
#SBATCH --output=hcvrp_dynamic_encoding_parco_test.log
#SBATCH --error=hcvrp_dynamic_encoding_parco_test.err
#SBATCH --mail-user=athota@uni-hildesheim.de
#SBATCH --mail-type=ALL
#SBATCH --partition=STUD
#SBATCH --gres=gpu:1


source .venv/bin/activate

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

RUN_GROUP=hcvrp_n100_m7
RUN_NAME=parco_dynamic_encoding
CKPT=$(ls -td logs/train/runs/${RUN_GROUP}/${RUN_NAME}/*/checkpoints/last.ckpt | head -n 1)
echo "Using checkpoint: ${CKPT}"

# Re-encoding makes inference much slower per step, so a smaller batch may be
# needed here too; drop to 64 or 32 if this OOMs.
srun python test.py \
  --problem hcvrp \
  --checkpoint "${CKPT}" \
  --decode_type sequential_greedy \
  --batch_size 128

#!/bin/bash
#SBATCH -p gpu
#SBATCH --mem=32g
#SBATCH --gres=gpu:rtx2080:1
#SBATCH -c 2
#SBATCH --output=example_1.out

source activate mlfold

folder_with_pdbs="/homes/55/anda/RFdiffusion/example_outputs/design_binders"

output_dir="../outputs/example_PDL1_outputs"
if [ ! -d $output_dir ]
then
    mkdir -p $output_dir
fi

path_for_parsed_chains=$output_dir"/parsed_pdbs.jsonl"

# python ../helper_scripts/parse_multiple_chains.py --input_path=$folder_with_pdbs --output_path=$path_for_parsed_chains

python ../protein_mpnn_run.py \
        --jsonl_path $path_for_parsed_chains \
        --fixed_positions_jsonl "/homes/55/anda/RFdiffusion/example_outputs/design_binders/fixed_positions_by_chain.json" \
        --out_folder $output_dir \
        --num_seq_per_target 1 \
        --sampling_temp "0.1" \
        --seed 37 \
        --batch_size 1

        # --chain_id_jsonl "/homes/55/anda/RFdiffusion/example_outputs/design_binders/chains_fixed_PDL1.json" \
# simergy-lm-tmo-alpha
https://huggingface.co/HishaamA/simergy-lm-tmo-alpha

A toolset for AI-driven material generation and property prediction. This project fine-tunes a Transformer-based  language model (Meta-Llama-3.1-8B) on the Materials Project dataset to architect promising Transition Metal Oxide (TMO) candidates for battery applications. The model natively generates crystal structures in the precise CIF formatting, which are subsequently filtered for stability via ALIGNN and structurally relaxed using the CHGNet Quantum Force Field.

## Features

- Structure Generation: Generates CIF text structures either unconditionally or through interactive material constraints.
- Prediction and Filtering: Evaluates predicted CIF files through ALIGNN to filter structures based on formation energy, band gap, and energy above convex hull, verifying novelty against the Materials Project.
- Fast Data Preprocessing: Converts raw CIF files and structural attributes into pre-tokenized parquet datasets to accelerate model training.
- Structural Relaxation: Applies automated structural optimization using CHGNet to relax generated atomic coordinates.
- Element Substitution: Identifies similar elements to perform structural substitutions within existing materials.

## Usage

- Generate Data: Use `python preprocess_data.py --input-dir data/basic` to create fast tokenized datasets.
- Train Model: Run `python train.py --run-name <run_name>` to fine-tune the causal language model via LoRA.
- Generate Materials: Execute `python generate.py --model_name 8b --model_path <path>` to construct new bulk materials.
- Filter: Use `python alignntest.py --output_dir <dir>` to evaluate generated structures and keep highly stable candidates.
- Relax: Run `python cif-relax.py` to physically stabilize selected CIF architectures.

## Requirements

Key dependencies include:
- PyTorch
- Transformers
- PEFT
- Pymatgen
- ALIGNN
- CHGNet
- matgl

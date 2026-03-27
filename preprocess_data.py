import os
import random
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from pymatgen.core.structure import Structure
from unsloth import FastLanguageModel

MAX_LENGTH = 2048
DEFAULT_PAD_TOKEN = "[PAD]"

def get_crystal_string(cif_str):
    structure = Structure.from_str(cif_str, fmt="cif")

    structure.translate_sites(
        indices=range(len(structure.sites)),
        vector=np.random.uniform(size=(3,))
    )

    lengths = structure.lattice.parameters[:3]
    angles = structure.lattice.parameters[3:]
    atom_ids = structure.species
    frac_coords = structure.frac_coords

    crystal_str = \
        " ".join(["{0:.1f}".format(x) for x in lengths]) + "\n" + \
        " ".join([str(int(x)) for x in angles]) + "\n" + \
        "\n".join([
            str(t) + "\n" + " ".join([
                "{0:.2f}".format(x) for x in c
            ]) for t, c in zip(atom_ids, frac_coords)
        ])

    return crystal_str

def setup_tokenizer():
    print("Loading tokenizer...")
    _, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Meta-Llama-3.1-8B",
        max_seq_length=MAX_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({"pad_token": DEFAULT_PAD_TOKEN})

    print(f"Tokenizer loaded. Vocab size: {len(tokenizer)}")
    return tokenizer

def create_generation_sample(row, w_attributes=True):
    prompt = "Below is a description of a bulk material. "
    all_attributes = [
        "formation_energy_per_atom",
        "band_gap",
        "e_above_hull",
        "spacegroup.number",
    ]

    num_attributes = random.randint(0, len(all_attributes))
    if num_attributes > 0 and w_attributes:
        attributes = random.sample(all_attributes, num_attributes)
        attributes = ["pretty_formula"] + attributes

        prompt_lookup = {
            "formation_energy_per_atom": "The formation energy per atom is",
            "band_gap": "The band gap is",
            "pretty_formula": "The chemical formula is",
            "e_above_hull": "The energy above the convex hull is",
            "elements": "The elements are",
            "spacegroup.number": "The spacegroup number is",
        }

        for attr in attributes:
            if attr == "elements":
                prompt += f"{prompt_lookup[attr]} {', '.join(row[attr])}. "
            elif attr in ["formation_energy_per_atom", "band_gap", "e_above_hull"]:
                prompt += f"{prompt_lookup[attr]} {round(float(row[attr]), 4)}. "
            else:
                prompt += f"{prompt_lookup[attr]} {row[attr]}. "

    prompt += (
        "Generate a description of the lengths and angles of the lattice vectors "
        "and then the element type and coordinates for each atom within the lattice:\n"
    )

    crystal_str = get_crystal_string(row['cif'])
    full_text = prompt + crystal_str + "</s>"

    return full_text

def create_infill_sample(row):
    prompt = (
        'Below is a partial description of a bulk material where one '
        'element has been replaced with the string "[MASK]":\n'
    )

    structure = Structure.from_str(row['cif'], fmt="cif")
    species = [str(s) for s in structure.species]
    species_to_remove = random.choice(species)

    crystal_string = get_crystal_string(row['cif'])
    partial_crystal_str = crystal_string.replace(species_to_remove, "[MASK]")

    infill_str = prompt + partial_crystal_str + "\n"
    infill_str += (
        "Generate an element that could replace [MASK] in the bulk material:\n"
    )
    infill_str += str(species_to_remove) + "</s>"

    return infill_str

def preprocess_split(csv_path, output_path, tokenizer, w_attributes=True, num_augmentations=1):
    print(f"Processing {csv_path}...")
    df = pd.read_csv(csv_path)

    output_rows = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing samples"):
        try:
            for aug_idx in range(num_augmentations):
                if random.random() < 0.66:
                    text = create_generation_sample(row, w_attributes)
                    task_type = "generation"
                else:
                    text = create_infill_sample(row)
                    task_type = "infill"

                tokens = tokenizer(
                    text,
                    return_tensors="pt",
                    max_length=MAX_LENGTH,
                    truncation=True,
                )
                input_ids = tokens.input_ids[0].tolist()

                output_rows.append({
                    'text': text,
                    'input_ids': input_ids,
                    'task_type': task_type,
                    'material_id': row.get('material_id', ''),
                    'pretty_formula': row.get('pretty_formula', ''),
                    'augmentation_idx': aug_idx
                })
        except Exception as e:
            print(f"Error processing sample {idx}: {e}")
            continue

    output_df = pd.DataFrame(output_rows)
    output_df.to_parquet(output_path, index=False)
    print(f"Saved {len(output_rows)} samples to {output_path}")
    print(f"Original samples: {len(df)}, Augmented samples: {len(output_rows)}")

def main(args):
    args.output_dir.mkdir(parents=True, exist_ok=True)

    random.seed(args.seed)
    np.random.seed(args.seed)

    tokenizer = setup_tokenizer()

    for split in ['train_v2', 'val_v2', 'test_v2']:
        input_path = args.input_dir / f"{split}.csv"
        if not input_path.exists():
            print(f"Skipping {split} - file not found")
            continue

        output_path = args.output_dir / f"{split}.parquet"
        preprocess_split(
            input_path,
            output_path,
            tokenizer,
            w_attributes=args.w_attributes,
            num_augmentations=args.num_augmentations
        )

    print("\nPreprocessing complete!")
    print(f"Preprocessed data saved to: {args.output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Preprocess CIF data for fast training"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/basic"),
        help="Directory containing train.csv, val.csv, test.csv"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/preprocessed"),
        help="Directory to save preprocessed parquet files"
    )
    parser.add_argument(
        "--w-attributes",
        type=int,
        default=1,
        help="Include attributes in prompts (1=yes, 0=no)"
    )
    parser.add_argument(
        "--num-augmentations",
        type=int,
        default=1,
        help="Number of random augmentations per sample (1=no augmentation, 5=5x data)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    main(args)

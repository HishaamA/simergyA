import os
import random
import argparse
import pandas as pd
import numpy as np
from pathlib import Path


import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig
)
from peft import PeftModel


from pymatgen.core import Structure
from pymatgen.core.lattice import Lattice


from train import (
    get_crystal_string,   
    MAX_LENGTH
)
from templating import make_swap_table

DEFAULT_PAD_TOKEN = "[PAD]"
DEFAULT_EOS_TOKEN = "</s>"
DEFAULT_BOS_TOKEN = "<s>"
DEFAULT_UNK_TOKEN = "<unk>"

def parse_fn(gen_str):
    lines = [x for x in gen_str.split("\n") if len(x) > 0]
    lengths = [float(x) for x in lines[0].split(" ")]
    angles = [float(x) for x in lines[1].split(" ")]
    species = [x for x in lines[2::2]]
    coords = [[float(y) for y in x.split(" ")] for x in lines[3::2]]
    
    structure = Structure(
        lattice=Lattice.from_parameters(*(lengths + angles)),
        species=species,
        coords=coords, 
        coords_are_cartesian=False,
    )
    
    return structure.to(fmt="cif")

def smart_tokenizer_and_embedding_resize(special_tokens_dict, llama_tokenizer, model):
    num_new_tokens = llama_tokenizer.add_special_tokens(special_tokens_dict)
    model.resize_token_embeddings(len(llama_tokenizer))

    if num_new_tokens > 0:
        input_embeddings = model.get_input_embeddings().weight.data
        output_embeddings = model.get_output_embeddings().weight.data

        input_embeddings_avg = input_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)
        output_embeddings_avg = output_embeddings[:-num_new_tokens].mean(dim=0, keepdim=True)

        input_embeddings[-num_new_tokens:] = input_embeddings_avg
        output_embeddings[-num_new_tokens:] = output_embeddings_avg

def prepare_model_and_tokenizer(args):
    print("\n--- Loading native Hugging Face model ---")
    
    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    
    base_model_name = "unsloth/Meta-Llama-3.1-8B"
    print(f"Loading tokenizer from {base_model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_name, 
        padding_side="left" 
    )
    
    print(f"Loading base model from {base_model_name}...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=quant_config,
        device_map="auto",
        dtype=torch.bfloat16,
    )
    
    
    print("Resizing base embeddings to match training vocabulary...")
    special_tokens_dict = {"pad_token": DEFAULT_PAD_TOKEN}
    smart_tokenizer_and_embedding_resize(
        special_tokens_dict=special_tokens_dict,
        llama_tokenizer=tokenizer,
        model=model
    )
    
    print(f"Loading trained weights from {args.model_path}...")
    model = PeftModel.from_pretrained(model, args.model_path)
    
    print("Model loaded successfully!\n")
    return model, tokenizer

def unconditional_sample(args):
    model, tokenizer = prepare_model_and_tokenizer(args)

    prompts = []
    for _ in range(args.num_samples):
        prompt = "Below is a description of a bulk material. "
        prompt += (
            "Generate a description of the lengths and angles of the lattice vectors "
            "and then the element type and coordinates for each atom within the lattice:\n"
        )
        prompts.append(prompt)
 
    outputs = []
    print(f"Generating {args.num_samples} crystal structures...")
    
    while len(outputs) < args.num_samples:
        batch_prompts = prompts[len(outputs):len(outputs)+args.batch_size]

        batch = tokenizer(
            list(batch_prompts), 
            return_tensors="pt",
            padding=True, 
        )
        batch = {k: v.to("cuda") for k, v in batch.items()}

        with torch.no_grad():
            generate_ids = model.generate(
                **batch,
                do_sample=True,
                max_new_tokens=500,
                temperature=args.temperature, 
                top_p=args.top_p,
                pad_token_id=tokenizer.pad_token_id, 
            )

        gen_strs = tokenizer.batch_decode(
            generate_ids, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )

        for gen_str, prompt in zip(gen_strs, batch_prompts):
            material_str = gen_str.replace(prompt, "")
            material_str = material_str.replace("</s>", "").replace("<|end_of_text|>", "").replace("<|eot_id|>", "").strip()

            try:
                cif_str = parse_fn(material_str)
                _ = Structure.from_str(cif_str, fmt="cif")
            except Exception as e:
                print(f"Failed to parse a generated structure: {e}")
                continue

            outputs.append({
                "gen_str": gen_str,
                "cif": cif_str,
                "model_name": args.model_name,
            })
            print(f"Successfully generated structure {len(outputs)}/{args.num_samples}")

    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)
    df = pd.DataFrame(outputs)
    df.to_csv(args.out_path, index=False)
    print(f"\nAll done! Saved {len(outputs)} structures to {args.out_path}")

def interactive_sample(args):
    model, tokenizer = prepare_model_and_tokenizer(args)

    user_constraint = input("\nEnter your material constraints:\n> ")
    
    prompts = []
    for _ in range(args.num_samples):
        prompt = f"Below is a description of a bulk material. {user_constraint}. "
        prompt += (
            "Generate a description of the lengths and angles of the lattice vectors "
            "and then the element type and coordinates for each atom within the lattice:\n"
        )
        prompts.append(prompt)
 
    outputs = []
    print(f"\nGenerating {args.num_samples} variations of your requested material...")
    
    while len(outputs) < args.num_samples:
        batch_prompts = prompts[len(outputs):len(outputs)+args.batch_size]

        batch = tokenizer(
            list(batch_prompts), 
            return_tensors="pt",
            padding=True,
        )
        batch = {k: v.to("cuda") for k, v in batch.items()}

        with torch.no_grad():
            generate_ids = model.generate(
                **batch,
                do_sample=True,
                max_new_tokens=500,
                temperature=args.temperature, 
                top_p=args.top_p,
                pad_token_id=tokenizer.pad_token_id, 
            )

        gen_strs = tokenizer.batch_decode(
            generate_ids, 
            skip_special_tokens=True, 
            clean_up_tokenization_spaces=False
        )

        for gen_str, prompt in zip(gen_strs, batch_prompts):
            material_str = gen_str.replace(prompt, "")
            
            material_str = material_str.replace("</s>", "").replace("<|end_of_text|>", "").replace("<|eot_id|>", "").strip()

            try:
                cif_str = parse_fn(material_str)
                _ = Structure.from_str(cif_str, fmt="cif")
            except Exception as e:
                print(f"Failed to parse: {e}")
                continue

            outputs.append({
                "prompt_used": user_constraint, 
                "gen_str": gen_str,
                "cif": cif_str,
                "model_name": args.model_name,
            })
            print(f"Successfully generated structure {len(outputs)}/{args.num_samples}")

    os.makedirs(os.path.dirname(args.out_path), exist_ok=True)
    df = pd.DataFrame(outputs)
    df.to_csv(args.out_path, index=False)
    print(f"\nAll done! Saved {len(outputs)} structures to {args.out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--num_samples", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--out_path", type=str, default="./outputs/llm_samples.csv")
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--conditions", type=str, default="pretty_formula")
    parser.add_argument("--conditions_file", type=str, default="")
    parser.add_argument("--infill_file", type=str, default="")
    parser.add_argument("--infill_do_constraint", type=int, default=0)
    parser.add_argument("--infill_constraint_tolerance", type=float, default=0.1)
    parser.add_argument("--fp4", action="store_true", default=False)
    parser.add_argument("--lora_rank", type=int, default=8)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--data_path", type=Path, default="data/basic")
    parser.add_argument("--num_epochs", type=int, default=25)
    parser.add_argument("--grad_accum", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--lr_scheduler", type=str, default="cosine")
    parser.add_argument("--num_warmup_steps", type=int, default=100)
    parser.add_argument("--weight_decay", type=float, default=0.0)
    parser.add_argument("--eval_freq", default=10000, type=int)
    parser.add_argument("--save_freq", default=5000, type=int)
    parser.add_argument("--w_attributes", type=int, default=1)
    parser.add_argument("--resume_dir", type=Path, default=None)
    parser.add_argument("--debug", action="store_true", default=False)
    args = parser.parse_args()

    if ".csv" in args.out_path:
        out_path = args.out_path
    else:
        i = os.environ.get("SLURM_ARRAY_TASK_ID", 0)
        out_path = os.path.join(args.out_path, f"samples_{i}.csv")
        args.out_path = out_path

    if args.conditions_file:
        pass
    elif args.infill_file:
        pass
    else:
        interactive_sample(args)
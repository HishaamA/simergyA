import os
import re
import subprocess
import argparse
import pandas as pd
from mp_api.client import MPRester
from pymatgen.core import Structure
from dotenv import load_dotenv

load_dotenv()
MP_API_KEY = "u5mvwnxEEfiupZl3ACSkfihDO52Wj1M1"

def identify_duplicates(cif_directory):
    print("--- Checking Materials Project for Duplicates ---")
    mp_flags = {}
    
    for filename in os.listdir(cif_directory):
        if not filename.endswith(".cif"):
            continue
            
        file_path = os.path.join(cif_directory, filename)
        
        try:
            struct = Structure.from_file(file_path)
            formula = struct.composition.reduced_formula
            
            with MPRester(MP_API_KEY) as mpr:
                docs = mpr.materials.summary.search(formula=formula)
                
                if docs:
                    print(f"Match found in MP for {formula} ({filename})")
                    mp_flags[filename] = True
                else:
                    print(f"Novel formula! {formula} ({filename})")
                    mp_flags[filename] = False
                    
        except Exception as e:
            print(f"Error parsing {filename}, flagging as Invalid. Error: {e}")
            mp_flags[filename] = "Invalid"
            
    return mp_flags

def batch_predict_alignn(cif_directory, mp_flags):
    results = []
    cif_files = [f for f in os.listdir(cif_directory) if f.endswith(".cif")]
    
    for filename in cif_files:
        file_path = os.path.join(cif_directory, filename)
        with open(file_path, 'r') as file:
            cif_content = file.read()
            
        results.append({
            "Name": filename,
            "Known_in_MP": mp_flags.get(filename, "Unknown"),
            "CIF": cif_content,
            "Formation Energy (eV/atom)": None,
            "Energy Above Hull (eV/atom)": None,
            "Band Gap (eV)": None 
        })
        
    df = pd.DataFrame(results)

    models = {
        "Formation Energy (eV/atom)": "jv_formation_energy_peratom_alignn",
        "Energy Above Hull (eV/atom)": "jv_ehull_alignn",
        "Band Gap (eV)": "jv_mbj_bandgap_alignn"
    }

    alignn_script = "alignn/alignn/pretrained.py"

    for property_name, model_name in models.items():
        print(f"\n--- Running ALIGNN Prediction for {property_name} ---")
        
        for filename in cif_files:
            file_path = os.path.join(cif_directory, filename)
            cmd = f"python {alignn_script} --model_name {model_name} --file_format cif --file_path {file_path}"
            
            try:
                print(f"Analyzing {filename}...")
                output = subprocess.check_output(cmd, shell=True, text=True)
                
                match = re.search(r"\[([-+]?\d*\.\d+|\d+)\]", output)
                if match:
                    value = float(match.group(1))
                    df.loc[df['Name'] == filename, property_name] = value
                
            except subprocess.CalledProcessError as e:
                print(f"Error processing {filename} with {model_name}: {e}")

    return df

def main(args):
    cif_directory = args.output_dir
    
    mp_flags = identify_duplicates(cif_directory)
    
    df = batch_predict_alignn(cif_directory, mp_flags)
    
    output_csv = os.path.join(os.getcwd(), "output.csv")
    df.to_csv(output_csv, index=False)
    print(f"\nRaw results saved to {output_csv}")

    print("\n--- Filtering for Highly Stable, Novel Candidates ---")
    filtered_df = df[
        (df['Known_in_MP'] == False) & 
        (df['Formation Energy (eV/atom)'] < -1.5) &
        (df['Energy Above Hull (eV/atom)'] < 0.08) & 
        (df['Band Gap (eV)'] <= 0.5)
    ]
    
    print(filtered_df[['Name', 'Formation Energy (eV/atom)', 'Energy Above Hull (eV/atom)', 'Band Gap (eV)']])
    
    filtered_output_path = os.path.join(os.getcwd(), "filtered_structures_unconditional.csv")
    filtered_df.to_csv(filtered_output_path, index=False)
    print(f"\nFiltered breakthrough candidates saved to {filtered_output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_dir', required=True, help="Path to the folder containing generated CIFs")
    args = parser.parse_args()
    main(args)
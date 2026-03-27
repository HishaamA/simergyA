import pandas as pd
from pymatgen.core import Structure
from pymatgen.io.cif import CifWriter
from tqdm import tqdm
import warnings

# Suppress pymatgen warnings so your terminal doesn't get spammed
warnings.filterwarnings('ignore')

def clean_dataset():
    print("Loading broken train.csv...")
    df = pd.read_csv("val.csv")
    
    fixed_cifs = []
    failed_count = 0
    
    print(f"Rebuilding physical symmetry for {len(df)} structures...")
    
    # tqdm gives us a nice loading bar in the terminal
    for index, row in tqdm(df.iterrows(), total=len(df)):
        try:
            # 1. Load the "dumb" P 1 structure from the CSV
            struct = Structure.from_str(str(row['cif']), fmt="cif")
            
            # 2. Use CifWriter with symprec=0.1. 
            # This forces pymatgen to calculate the TRUE symmetry (e.g., R-3m, Fd-3m) 
            # and write the proper 120-degree hexagonal / trigonal angles if they exist.
            writer = CifWriter(struct, symprec=0.1)
            good_cif = writer.write_string()
            
            fixed_cifs.append(good_cif)
            
        except Exception as e:
            # If a structure is completely corrupted, just keep the old one so we don't crash
            fixed_cifs.append(row['cif'])
            failed_count += 1

    # Overwrite the bad column with our new, physically accurate CIFs
    df['cif'] = fixed_cifs
    
    print(f"\nFinished processing! (Failed to parse {failed_count} corrupted structures)")
    
    output_filename = "val_v2.csv"
    df.to_csv(output_filename, index=False)
    print(f"✅ Saved perfectly symmetrized dataset to {output_filename}!")

if __name__ == "__main__":
    clean_dataset()
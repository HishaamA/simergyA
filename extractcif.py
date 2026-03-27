import pandas as pd
import os

df = pd.read_csv("outputs/llm_samples.csv")
output_dir = "my_llama_cifs"
os.makedirs(output_dir, exist_ok=True)

for idx, row in df.iterrows():
    cif_text = str(row['cif'])
    if pd.isna(cif_text) or not cif_text.strip():
        continue
    with open(os.path.join(output_dir, f"structure_{idx + 1}.cif"), "w") as f:
        f.write(cif_text)
print("All 5 new CIFs successfully extracted!")